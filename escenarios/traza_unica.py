#!/usr/bin/env python3
"""TRAZA ÚNICA: un solo hecho de negocio de punta a punta, para sustentación.

Publica UN comando CrearCotizacion, espera su evento, publica UN comando
AceptarCotizacion y sigue el hecho por los cuatro servicios:
  comandos-cotizacion -> cotizaciones -> eventos-cotizacion -> pagos ->
  eventos-pago -> trabajos -> eventos-trabajo -> notificaciones
Al final muestra el estado en cada servicio y la historia del event store.

Uso:
  Docker:  docker compose run --rm escenarios python traza_unica.py
  Dev:     BROKER=archivo BROKER_DIR=$PWD/../broker_dev python traza_unica.py
Mientras corre, en otra terminal:
  docker compose logs -f cotizaciones pagos trabajos notificaciones | grep -E "\\[uow\\]|\\[cotizaciones\\]|\\[pagos\\]|\\[trabajos\\]|\\[notificaciones\\]"
"""
import json
import os
import threading
import time
import uuid

from comun import broker_mod, contratos, get, esperar, COTIZACIONES, PAGOS, NOTIFICACIONES

TRABAJOS = os.getenv("URL_TRABAJOS", "http://localhost:5004")
PAIS = os.getenv("PAIS", "AR")
MONEDA = os.getenv("MONEDA", "ARS")
MONTO = float(os.getenv("MONTO", "180000"))
ID_TRABAJO = f"TRB-DEMO-{uuid.uuid4().hex[:4].upper()}"

bk = broker_mod.broker()
visto = {}


def observar(msg):
    d = msg.get("data", {})
    if d.get("id_trabajo") == ID_TRABAJO and msg["type"] not in visto:
        visto[msg["type"]] = msg


threading.Thread(target=lambda: broker_mod.broker().consumir(
    "eventos-cotizacion", f"traza-{uuid.uuid4().hex[:6]}", observar), daemon=True).start()
time.sleep(1.0)

print(f"\n== TRAZA ÚNICA · trabajo {ID_TRABAJO} · {MONTO:,.0f} {MONEDA} · pais {PAIS} ==\n")

print("1) COMANDO CrearCotizacion  ->  tópico comandos-cotizacion")
bk.publicar("comandos-cotizacion", contratos.comando_crear_cotizacion(
    ID_TRABAJO, "PRV-42", MONTO, MONEDA, pais=PAIS))
esperar(lambda: "CotizacionCreada" in visto, timeout=30, descripcion="CotizacionCreada")
ev = visto["CotizacionCreada"]
id_cot = ev["data"]["id_cotizacion"]
print(f"   <- EVENTO CotizacionCreada {ev['specversion']} · id_cotizacion = {id_cot}")

print("2) COMANDO IniciarSagaAceptacion  ->  tópico comandos-saga  (el orquestador envía AceptarCotizacion)")
bk.publicar("comandos-saga", contratos.comando_iniciar_saga(id_cot, ID_TRABAJO, "PRV-42", MONTO, MONEDA, PAIS))
esperar(lambda: "CotizacionAceptada" in visto, timeout=30, descripcion="CotizacionAceptada")
ev = visto["CotizacionAceptada"]
print(f"   <- EVENTO CotizacionAceptada {ev['specversion']} (pais={ev['data'].get('pais')})  ->  tópico eventos-cotizacion")

print("3) PAGOS consume CotizacionAceptada -> comando RetenerPago -> EVENTO PagoRetenido v1 -> eventos-pago")
esperar(lambda: any(r["id_cotizacion"] == id_cot for r in get(PAGOS + "/reservas")),
        timeout=30, descripcion="reserva de pago")
reserva = next(r for r in get(PAGOS + "/reservas") if r["id_cotizacion"] == id_cot)
print(f"   reserva {reserva['id'][:8]}… {reserva['monto']:,.0f} {reserva['moneda']} estado={reserva['estado']} pais={reserva['pais']}")

print("4) TRABAJOS consume PagoRetenido -> comando AgendarTrabajo -> EVENTO TrabajoAgendado v1 -> eventos-trabajo")
esperar(lambda: any(t["id_cotizacion"] == id_cot for t in get(TRABAJOS + "/trabajos")),
        timeout=30, descripcion="trabajo agendado")
trabajo = next(t for t in get(TRABAJOS + "/trabajos") if t["id_cotizacion"] == id_cot)
print(f"   agenda {trabajo['id'][:8]}… trabajo={trabajo['id_trabajo']} pago={trabajo['id_pago'][:8]}… estado={trabajo['estado']}")

print("5) NOTIFICACIONES consume los tres eventos")
esperar(lambda: sum(1 for n in get(NOTIFICACIONES + "/notificaciones")
                    if id_cot[:8] in n["mensaje"] or ID_TRABAJO in n["mensaje"]) >= 2,
        timeout=30, descripcion="notificaciones")
notifs = [n for n in get(NOTIFICACIONES + "/notificaciones") if id_cot[:8] in n["mensaje"] or ID_TRABAJO in n["mensaje"]]
for n in notifs:
    print(f"   [{n['tipo']} {n['version']}] -> {n['destinatario']}: {n['mensaje']}")

print("\n6) EVENT SOURCING en cotizaciones (GET /cotizaciones/<id>/historia)")
h = get(f"{COTIZACIONES}/cotizaciones/{id_cot}/historia")
for e in h["historia"]:
    print(f"   seq {e['seq']}  {e['tipo']:<20} {e['version']}")
r = h["reconstruida_por_replay"]
print(f"   reconstruida por replay: estado={r['estado']} pais={r['pais']} version={r['version']}")

print("\n7) SAGA LOG del orquestador (GET /sagas/<id_cotizacion>/log)")
SAGA = os.getenv("URL_SAGA", "http://localhost:5005")
esperar(lambda: get(f"{SAGA}/sagas/{id_cot}")["estado"] == "COMPLETADA", timeout=30, descripcion="saga completada")
sg = get(f"{SAGA}/sagas/{id_cot}/log")
print(f"   saga {sg['id_saga'][:8]}… estado {sg['estado']}")
for e in sg["log"]:
    print(f"   {e['secuencia']:>2}  {e['tipo']:<22} {(e['paso'] or ''):<20} {(e['servicio'] or ''):<13} {e['mensaje']}")

print(f"\n== FIN · id_cotizacion = {id_cot} ==")
print(f"   curl localhost:5001/cotizaciones/{id_cot}/historia")
