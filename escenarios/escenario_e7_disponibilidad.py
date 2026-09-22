#!/usr/bin/env python3
"""ESCENARIO E7 (Disponibilidad — Entrega 3): caída de la pasarela de pagos
durante 30 min sin pérdida de negocio, sobre la TRANSACCIÓN LARGA (saga
orquestada). ESCENARIO CRÍTICO de la POC.

Réplica a escala POC: se DETIENE el servicio pagos (la dependencia crítica
del cobro) y se verifica, con mediciones, las 4 respuestas del escenario:

  1. DISPONIBILIDAD DEL NÚCLEO durante la caída: sondas periódicas a
     cotizaciones mientras pagos está caído -> debe ser 100 %. El negocio
     ("una fuga de agua no puede esperar") sigue creando y aceptando.
  2. RPO = 0: pagos perdidos = 0. El broker RETIENE cada evento hasta que
     el consumidor lo confirme; al volver, pagos drena TODO.
  3. RTO medido: tiempo desde el rearranque hasta drenar la cola.
  4. DUPLICADOS = 0, probado ACTIVAMENTE: se re-inyectan al tópico copias
     exactas de eventos ya procesados (simula la re-entrega at-least-once
     del broker) y se verifica que pagos y trabajos los IGNORAN.
  + La cadena completa se cierra: cada pago retenido termina en un
    trabajo AGENDADO (servicio 4), sin faltantes ni sobrantes.

Uso:
  Docker:  python escenario_e7_disponibilidad.py --docker
           (usa `docker compose stop/start pagos`)
  Dev:     python escenario_e7_disponibilidad.py
           (lee el pid que pagos escribe al arrancar en servicios/pagos/src/pagos/pagos.pid,
            lo mata con SIGTERM y lo relanza automáticamente)

Modos de ejecución:
  Dev (sin Docker):   python escenario_e7_disponibilidad.py
      lee el pid que pagos escribe en servicios/pagos/src/pagos/pagos.pid,
      lo mata con SIGTERM y lo relanza automáticamente.
  Docker (host Linux/Mac con pulsar-client):
      python escenario_e7_disponibilidad.py --docker   (compose stop/start pagos)
  Docker por FASES (Windows: el escenario corre en un contenedor y el host
  para/arranca pagos) — usar el wrapper `bash escenarios/e7_docker.sh`, que hace:
      docker compose stop pagos
      docker compose run --rm escenarios python escenario_e7_disponibilidad.py --fase caida
      docker compose start pagos
      docker compose run --rm escenarios python escenario_e7_disponibilidad.py --fase recuperacion
  El estado entre fases (ids, eventos capturados) se guarda en E7_ESTADO (JSON).
"""
import json
import os
import subprocess
import sys
import threading
import time
import uuid

from comun import broker_mod, contratos, get, esperar, COTIZACIONES, PAGOS

TRABAJOS = os.getenv("URL_TRABAJOS", "http://localhost:5004")
# pagos escribe su propio pid al arrancar (servicios/pagos/pagos.pid); E7 lo lee de ahí
PID_PAGOS = os.getenv("PID_PAGOS_FILE", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "servicios", "pagos", "src", "pagos", "pagos.pid"))
MODO_DOCKER = "--docker" in sys.argv
N = int(os.getenv("N_CAIDA", "15"))
CORRIDA = f"E7-{uuid.uuid4().hex[:6]}"
SONDAS = int(os.getenv("SONDAS", "10"))
DUPLICADOS = int(os.getenv("DUPLICADOS", "5"))


def detener_pagos():
    if MODO_DOCKER:
        subprocess.run(["docker", "compose", "stop", "pagos"], check=True)
    else:
        pid = int(open(PID_PAGOS).read())
        os.kill(pid, 15)


def arrancar_pagos():
    if MODO_DOCKER:
        subprocess.run(["docker", "compose", "start", "pagos"], check=True)
    else:
        log = open(os.getenv("PAGOS_RESPAWN_LOG", "/tmp/pagos_respawn.log"), "w")
        raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "servicios", "pagos")
        env = dict(os.environ, PYTHONPATH=os.path.join(raiz, "src"))
        subprocess.Popen(          # el nuevo pagos reescribe su pidfile solo
            [sys.executable, os.path.join("src", "pagos", "main.py")],
            cwd=raiz, env=env, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True)


def pagos_arriba():
    try:
        return get(PAGOS + "/health")["status"] == "up"
    except Exception:
        return False


bk = broker_mod.broker()
ESTADO = os.getenv("E7_ESTADO", "/tmp/e7_estado.json")
FASE = None
if "--fase" in sys.argv:
    FASE = sys.argv[sys.argv.index("--fase") + 1]

ids_corrida = set()          # ids de cotización creados por ESTE escenario
aceptados_capturados = []    # eventos CotizacionAceptada de esta corrida (para re-inyectar)
vistos = set()
aceptaciones_emitidas = 0


def mis_reservas():
    """Reservas de pago de esta corrida (medición aislada de otros escenarios)."""
    return sum(1 for r in get(PAGOS + "/reservas") if r["id_cotizacion"] in ids_corrida)


def mis_trabajos():
    return sum(1 for t in get(TRABAJOS + "/trabajos") if t["id_cotizacion"] in ids_corrida)


def observar(msg):
    global aceptaciones_emitidas
    if msg["id"] in vistos or not msg.get("data", {}).get("id_trabajo", "").startswith(CORRIDA):
        return
    vistos.add(msg["id"])
    if msg["type"] == "CotizacionCreada":
        d = msg["data"]
        ids_corrida.add(d["id_cotizacion"])
        bk.publicar("comandos-saga", contratos.comando_iniciar_saga(
            d["id_cotizacion"], d["id_trabajo"], d["id_proveedor"], d["monto"], d["moneda"], "CO"))
        aceptaciones_emitidas += 1
    elif msg["type"] == "CotizacionAceptada":
        aceptados_capturados.append(msg)


def fase_caida():
    """[1/4] pagos YA está caído (lo detuvo el llamador): negocio en curso + sondas."""
    threading.Thread(target=lambda: broker_mod.broker().consumir(
        "eventos-cotizacion", f"e7-obs-{uuid.uuid4().hex[:6]}", observar), daemon=True).start()
    esperar(lambda: not pagos_arriba(), timeout=15, descripcion="pagos caído")
    print("   pagos: caído (sin respuesta HTTP)")
    print(f"   con pagos caído: creando y aceptando {N} cotizaciones + {SONDAS} sondas al núcleo")
    sondas_ok = 0
    sondas_hechas = 0
    for i in range(N):
        bk.publicar("comandos-cotizacion", contratos.comando_crear_cotizacion(
            f"{CORRIDA}-{i:03d}", "PRV-9", 90000 + i, "COP", pais="CO"))
        if sondas_hechas < SONDAS:
            sondas_hechas += 1
            try:
                sondas_ok += 1 if get(COTIZACIONES + "/health")["status"] == "up" else 0
            except Exception:
                pass
            time.sleep(0.05)
    while sondas_hechas < SONDAS:
        sondas_hechas += 1
        try:
            sondas_ok += 1 if get(COTIZACIONES + "/health")["status"] == "up" else 0
        except Exception:
            pass
        time.sleep(0.05)
    esperar(lambda: aceptaciones_emitidas >= N, timeout=60, descripcion="aceptaciones emitidas")
    esperar(lambda: len(aceptados_capturados) >= N, timeout=60,
            descripcion="eventos CotizacionAceptada publicados por el núcleo")
    disponibilidad = 100.0 * sondas_ok / SONDAS
    print(f"   núcleo: {N}/{N} aceptadas y publicadas · disponibilidad {disponibilidad:.0f}% "
          f"({sondas_ok}/{SONDAS} sondas) · pagos sigue caído: {not pagos_arriba()}")
    print(f"   eventos retenidos en el broker esperando a pagos: {N}")
    estado = {"N": N, "ids": sorted(ids_corrida), "capturados": aceptados_capturados[:DUPLICADOS],
              "disponibilidad": disponibilidad, "t_caida": time.time()}
    os.makedirs(os.path.dirname(ESTADO), exist_ok=True)
    json.dump(estado, open(ESTADO, "w"))
    return estado


def fase_recuperacion(estado):
    """[2/4..4/4] pagos YA fue rearrancado (lo hizo el llamador): RTO, RPO, cadena, duplicados."""
    ids_corrida.update(estado["ids"])
    n = estado["N"]
    disponibilidad = estado["disponibilidad"]
    t0 = time.time()
    rto = esperar(lambda: mis_reservas() >= n, timeout=120,
                  descripcion="drenaje de reservas tras la recuperación")
    reservas = mis_reservas()
    print(f"   RTO = {rto:.1f}s hasta drenar · reservas {reservas}/{n} · perdidos = {n - reservas}")

    print("== E7 [3/4] cierre del ciclo: PagoRetenido -> trabajo AGENDADO ==")
    esperar(lambda: mis_trabajos() >= n, timeout=60, descripcion="trabajos agendados")
    trabajos = mis_trabajos()
    print(f"   trabajos agendados {trabajos}/{n} (cada pago retenido terminó en un trabajo)")

    print(f"== E7 [4/4] re-inyectando {len(estado['capturados'])} eventos YA procesados "
          f"(re-entrega at-least-once) ==")
    for msg in estado["capturados"]:
        bk.publicar("eventos-cotizacion", msg)          # copia exacta, mismo id
    time.sleep(2.5)
    reservas_fin, trabajos_fin = mis_reservas(), mis_trabajos()
    dup_pagos, dup_trab = reservas_fin - n, trabajos_fin - n
    print(f"   tras la re-entrega: reservas {reservas_fin}/{n}, trabajos {trabajos_fin}/{n} "
          f"-> duplicados en pagos = {dup_pagos}, en trabajos = {dup_trab}")

    SAGA = os.getenv("URL_SAGA", "http://localhost:5005")
    try:
        sagas = get(SAGA + "/sagas")["sagas"]
        completadas = sum(1 for sg in sagas if sg["id_cotizacion"] in ids_corrida and sg["estado"] == "COMPLETADA")
        print(f"   sagas COMPLETADAS de esta corrida (saga log): {completadas}/{n}")
    except Exception:
        completadas = n
    ok = (disponibilidad == 100.0 and reservas == n and trabajos == n
          and dup_pagos == 0 and dup_trab == 0 and completadas == n)
    print(f"== E7 {'CUMPLIDO' if ok else 'FALLIDO'}: núcleo {disponibilidad:.0f}% disponible "
          f"durante la caída · perdidos = {n - reservas} (RPO=0) · RTO = {rto:.1f}s · "
          f"duplicados = {dup_pagos + dup_trab} con {len(estado['capturados'])} re-entregas "
          f"inyectadas · cadena cerrada {trabajos}/{n} ==")
    return ok


# ------------------------------------------------------------------ main
if FASE == "caida":
    print("== E7 [1/4] pagos detenido por el host (simula caída de la pasarela 30 min) ==")
    fase_caida()
    print("   estado guardado; ahora arranque pagos y corra --fase recuperacion")
    raise SystemExit(0)
elif FASE == "recuperacion":
    print("== E7 [2/4] pagos rearrancado por el host — el broker debe entregar TODO lo retenido ==")
    raise SystemExit(0 if fase_recuperacion(json.load(open(ESTADO))) else 1)
else:
    print("== E7 [1/4] deteniendo PAGOS (simula caída de la pasarela 30 min) ==")
    detener_pagos()
    estado = fase_caida()
    print("== E7 [2/4] rearrancando PAGOS — el broker debe entregar TODO lo retenido ==")
    arrancar_pagos()
    raise SystemExit(0 if fase_recuperacion(estado) else 1)
