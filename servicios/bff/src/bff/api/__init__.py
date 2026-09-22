"""BFF (Backend for Frontend) de Hogar de los Alpes — puerto 5000.

Es la ÚNICA puerta síncrona del sistema para clientes (app, partners,
Postman). Reglas de diseño:
- Las escrituras (POST) NO ejecutan lógica de negocio: publican COMANDOS a
  los tópicos de Apache Pulsar y responden 202 Accepted con el id del
  recurso y la ruta donde consultarlo. El resultado se ve después (CQS +
  consistencia eventual).
- Las lecturas (GET) son queries síncronas HTTP a los servicios — la única
  comunicación síncrona permitida. El BFF compone vistas (p. ej. el estado
  consolidado de la transacción larga) para que el cliente haga UNA llamada
  en vez de cuatro.
- El BFF no tiene base de datos ni reglas: es capa de presentación.
"""
import json
import os
import uuid
import urllib.request
from urllib.error import HTTPError, URLError

from flask import Flask, jsonify, request

from bff.infraestructura import broker as broker_mod
from bff.infraestructura import contratos

URLS = {
    "cotizaciones": os.getenv("URL_COTIZACIONES", "http://localhost:5001"),
    "pagos": os.getenv("URL_PAGOS", "http://localhost:5002"),
    "notificaciones": os.getenv("URL_NOTIFICACIONES", "http://localhost:5003"),
    "trabajos": os.getenv("URL_TRABAJOS", "http://localhost:5004"),
    "saga": os.getenv("URL_SAGA", "http://localhost:5005"),
}

TOPICOS = {"CrearCotizacion": "comandos-cotizacion", "AceptarCotizacion": "comandos-cotizacion",
           "RetenerPago": "comandos-pago", "AgendarTrabajo": "comandos-trabajo",
           "IniciarSagaAceptacion": "comandos-saga"}


def _get(servicio, ruta):
    """Query síncrona a un servicio. Devuelve (cuerpo, status)."""
    try:
        with urllib.request.urlopen(URLS[servicio] + ruta, timeout=5) as r:
            return json.loads(r.read()), r.status
    except HTTPError as e:
        try:
            return json.loads(e.read() or b"{}"), e.code
        except Exception:
            return {"error": f"HTTP {e.code}"}, e.code
    except URLError as e:
        return {"error": f"{servicio} no disponible: {e.reason}"}, 503


def create_app():
    app = Flask(__name__)
    bk = broker_mod.broker()

    def aceptado(comando, id_recurso, consulta):
        """Publica el comando y responde 202 (aceptado para procesar)."""
        bk.publicar(TOPICOS[comando["type"]], comando)
        print(f"[bff] COMANDO {comando['type']} publicado en '{TOPICOS[comando['type']]}' "
              f"(id_comando={comando['id'][:8]}…)")
        return jsonify({"estado": "ACEPTADO", "comando": comando["type"], "id": id_recurso,
                        "id_comando": comando["id"], "topico": TOPICOS[comando["type"]],
                        "consultar_en": consulta}), 202

    # ------------------------------------------------------------ salud
    @app.get("/bff/health")
    def health():
        estado = {"bff": "up"}
        for s in URLS:
            cuerpo, code = _get(s, "/health")
            estado[s] = cuerpo.get("status", "down") if code == 200 else "down"
        ok = all(v == "up" for v in estado.values())
        return jsonify(estado), 200 if ok else 503

    # ------------------------------------------- flujo principal (comandos)
    @app.post("/bff/cotizaciones")
    def crear_cotizacion():
        d = request.get_json(force=True, silent=True) or {}
        faltan = [k for k in ("id_trabajo", "id_proveedor", "monto", "moneda") if k not in d]
        if faltan:
            return jsonify({"error": f"faltan campos: {faltan}"}), 400
        id_cot = str(uuid.uuid4())
        cmd = contratos.crear_cotizacion(id_cot, d["id_trabajo"], d["id_proveedor"],
                                         float(d["monto"]), d["moneda"], d.get("pais", "CO"))
        return aceptado(cmd, id_cot, f"/bff/cotizaciones/{id_cot}")

    @app.post("/bff/cotizaciones/<id_cot>/aceptar")
    def aceptar_cotizacion(id_cot):
        """Capacidad de negocio 'aceptar cotización' = TRANSACCIÓN LARGA (saga
        orquestada): aceptar → retener pago → agendar trabajo, con compensación.
        Publica IniciarSagaAceptacion al orquestador; responde 202 con id_saga."""
        cot, code = _get("cotizaciones", f"/cotizaciones/{id_cot}")
        if code != 200:
            return jsonify({"error": "la cotización no existe (o aún no se procesó su creación)"}), 404
        id_saga = str(uuid.uuid4())
        datos = {k: cot.get(k) for k in ("id_trabajo", "id_proveedor", "monto", "moneda", "pais")}
        cmd = contratos.iniciar_saga_aceptacion(id_saga, id_cot, datos)
        bk.publicar(TOPICOS[cmd["type"]], cmd)
        print(f"[bff] COMANDO IniciarSagaAceptacion publicado en 'comandos-saga' (saga {id_saga[:8]}…)")
        return jsonify({"estado": "ACEPTADO", "comando": "IniciarSagaAceptacion", "id": id_cot,
                        "id_saga": id_saga, "id_comando": cmd["id"], "topico": "comandos-saga",
                        "consultar_en": f"/bff/sagas/{id_saga}",
                        "estado_consolidado_en": f"/bff/cotizaciones/{id_cot}/estado"}), 202

    @app.post("/bff/cotizaciones/<id_cot>/aceptar-sin-saga")
    def aceptar_sin_saga(id_cot):
        """Solo para pruebas: publica AceptarCotizacion directo (sin transacción larga)."""
        return aceptado(contratos.aceptar_cotizacion(id_cot), id_cot,
                        f"/bff/cotizaciones/{id_cot}")

    # ------------------------------------------ sagas (monitoreo de transacciones)
    @app.get("/bff/sagas")
    def sagas():
        cuerpo, code = _get("saga", "/sagas")
        return jsonify(cuerpo), code

    @app.get("/bff/sagas/log")
    def saga_log_global():
        n = request.args.get("n", "50")
        cuerpo, code = _get("saga", f"/sagas/log?n={n}")
        return jsonify(cuerpo), code

    @app.get("/bff/sagas/<ref>")
    def saga_por_ref(ref):
        cuerpo, code = _get("saga", f"/sagas/{ref}")
        return jsonify(cuerpo), code

    @app.get("/bff/sagas/<ref>/log")
    def saga_log(ref):
        cuerpo, code = _get("saga", f"/sagas/{ref}/log")
        return jsonify(cuerpo), code

    # ------------------------ comandos directos a otros servicios (saga E5)
    @app.post("/bff/pagos/retener")
    def retener_pago():
        d = request.get_json(force=True, silent=True) or {}
        faltan = [k for k in ("id_cotizacion", "id_trabajo", "monto", "moneda") if k not in d]
        if faltan:
            return jsonify({"error": f"faltan campos: {faltan}"}), 400
        cmd = contratos.retener_pago(d["id_cotizacion"], d["id_trabajo"], float(d["monto"]),
                                     d["moneda"], d.get("pais", "CO"))
        return aceptado(cmd, d["id_cotizacion"], "/bff/reservas")

    @app.post("/bff/trabajos/agendar")
    def agendar_trabajo():
        d = request.get_json(force=True, silent=True) or {}
        faltan = [k for k in ("id_trabajo", "id_cotizacion", "id_pago") if k not in d]
        if faltan:
            return jsonify({"error": f"faltan campos: {faltan}"}), 400
        cmd = contratos.agendar_trabajo(d["id_trabajo"], d["id_cotizacion"], d["id_pago"],
                                        d.get("pais", "CO"))
        return aceptado(cmd, d["id_trabajo"], "/bff/trabajos")

    # ----------------------------------------------- queries (síncronas)
    @app.get("/bff/cotizaciones/<id_cot>")
    def cotizacion(id_cot):
        cuerpo, code = _get("cotizaciones", f"/cotizaciones/{id_cot}")
        return jsonify(cuerpo), code

    @app.get("/bff/cotizaciones/<id_cot>/historia")
    def historia(id_cot):
        cuerpo, code = _get("cotizaciones", f"/cotizaciones/{id_cot}/historia")
        return jsonify(cuerpo), code

    @app.get("/bff/cotizaciones/<id_cot>/estado")
    def estado_consolidado(id_cot):
        """Vista compuesta de la transacción larga: cotización + pago + trabajo + notificaciones."""
        cot, code = _get("cotizaciones", f"/cotizaciones/{id_cot}")
        if code != 200:
            return jsonify({"id_cotizacion": id_cot, "fase": "NO_EXISTE_O_PENDIENTE",
                            "detalle": cot}), code
        reservas, _ = _get("pagos", "/reservas")
        trabajos, _ = _get("trabajos", "/trabajos")
        notifs, _ = _get("notificaciones", "/notificaciones")
        reserva = next((r for r in reservas if isinstance(r, dict)
                        and r.get("id_cotizacion") == id_cot), None) if isinstance(reservas, list) else None
        trabajo = next((t for t in trabajos if isinstance(t, dict)
                        and t.get("id_cotizacion") == id_cot), None) if isinstance(trabajos, list) else None
        mias = [n for n in notifs if isinstance(n, dict) and (
            id_cot[:8] in n.get("mensaje", "") or cot.get("id_trabajo", "\0") in n.get("mensaje", ""))] \
            if isinstance(notifs, list) else []
        saga, scode = _get("saga", f"/sagas/{id_cot}")
        saga = saga if scode == 200 else None
        if saga and saga.get("estado") in ("COMPENSADA", "COMPENSANDO", "FALLIDA"):
            fase = saga["estado"]
        elif trabajo and trabajo.get("estado") == "AGENDADO":
            fase = "TRABAJO_AGENDADO"
        elif reserva and reserva.get("estado") == "RETENIDO":
            fase = "PAGO_RETENIDO"
        elif cot.get("estado") == "ACEPTADA":
            fase = "ACEPTADA"
        else:
            fase = "EMITIDA"
        resumen_saga = None
        if saga:
            resumen_saga = {k: saga.get(k) for k in ("id_saga", "estado", "paso_actual",
                                                     "pasos_completados", "motivo_fallo", "entradas_log")}
        return jsonify({"id_cotizacion": id_cot, "fase": fase, "saga": resumen_saga, "cotizacion": cot,
                        "pago": reserva, "trabajo": trabajo, "notificaciones": mias})

    @app.get("/bff/reservas")
    def reservas():
        cuerpo, code = _get("pagos", "/reservas")
        return jsonify(cuerpo), code

    @app.get("/bff/trabajos")
    def trabajos():
        cuerpo, code = _get("trabajos", "/trabajos")
        return jsonify(cuerpo), code

    @app.get("/bff/notificaciones")
    def notificaciones():
        cuerpo, code = _get("notificaciones", "/notificaciones")
        return jsonify(cuerpo), code

    @app.get("/bff/stats")
    def stats():
        salida = {}
        for s, ruta in (("cotizaciones", "/cotizaciones/stats"), ("pagos", "/stats"),
                        ("trabajos", "/stats"), ("notificaciones", "/stats"), ("saga", "/sagas/stats")):
            cuerpo, _ = _get(s, ruta)
            salida[s] = cuerpo
        return jsonify(salida)

    return app
