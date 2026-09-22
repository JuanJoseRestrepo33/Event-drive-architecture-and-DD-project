#!/usr/bin/env python3
"""ESCENARIO E1 (Escalabilidad — Entrega 3): pico de creación masiva sobre la
transacción larga (saga orquestada: aceptar -> retener pago -> agendar trabajo).

Réplica a escala POC del pico climático 4x: se inyecta una ráfaga de N
COMANDOS CrearCotizacion al tópico de comandos, cada creación se acepta
(comando AceptarCotizacion) y se verifica que:
  1. Ninguna petición se rechaza (buffering: el broker absorbe la ráfaga).
  2. El sistema DRENA el pico end-to-end: pagos alcanza N reservas.
  3. Sin duplicados (consumidor idempotente): reservas == N exactamente.
Métricas: throughput de publicación y tiempo de drenaje.
"""
import os
import threading
import time
import uuid

from comun import broker_mod, contratos, get, esperar, PAGOS, NOTIFICACIONES

N = int(os.getenv("N", "60"))
CORRIDA = f"E1-{uuid.uuid4().hex[:6]}"

bk = broker_mod.broker()
base_pagos = get(PAGOS + "/stats")["reservas"]

vistos = set()

def aceptar_creadas(msg):
    if (msg.get("type") == "CotizacionCreada"
            and msg["data"]["id_trabajo"].startswith(CORRIDA)
            and msg["id"] not in vistos):
        vistos.add(msg["id"])
        d = msg["data"]
        bk.publicar("comandos-saga", contratos.comando_iniciar_saga(
            d["id_cotizacion"], d["id_trabajo"], d["id_proveedor"], d["monto"], d["moneda"], "CO"))

# el observador se suscribe ANTES de publicar (una suscripción nueva en Pulsar
# arranca en Earliest, pero suscribir primero evita cualquier carrera)
threading.Thread(target=lambda: broker_mod.broker().consumir(
    "eventos-cotizacion", f"e1-acceptor-{uuid.uuid4().hex[:6]}", aceptar_creadas),
    daemon=True).start()
time.sleep(1.0)

print(f"== E1: ráfaga de {N} comandos CrearCotizacion (pico 4x a escala POC) ==")
t0 = time.time()
for i in range(N):
    bk.publicar("comandos-cotizacion", contratos.comando_crear_cotizacion(
        f"{CORRIDA}-{i:04d}", f"PRV-{i % 7}", 100000 + i, "COP", pais="CO"))
t_pub = time.time() - t0
print(f"   publicados {N} en {t_pub:.2f}s ({N / t_pub:,.0f} comandos/s) — "
      f"0 rechazos (el broker encola)")
print("   iniciando la TRANSACCIÓN LARGA (saga) por cada cotización creada de esta corrida...")

dur = esperar(lambda: get(PAGOS + "/stats")["reservas"] >= base_pagos + N,
              timeout=180, descripcion=f"{N} reservas de pago")
total = get(PAGOS + "/stats")["reservas"] - base_pagos
notif = get(NOTIFICACIONES + "/stats")["notificaciones"]
print(f"   drenaje end-to-end: {total} reservas en {dur:.1f}s · "
      f"notificaciones acumuladas: {notif}")
ok = total == N
print(f"== E1 {'CUMPLIDO' if ok else 'FALLIDO'}: 0 rechazos, drenaje completo, "
      f"reservas exactas {total}/{N} (idempotencia) ==")
raise SystemExit(0 if ok else 1)
