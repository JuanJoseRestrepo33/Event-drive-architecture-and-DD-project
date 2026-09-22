"""Consumidores del orquestador:
- `comandos-saga`: IniciarSagaAceptacion (lo publica el BFF).
- `eventos-cotizacion`, `eventos-pago`, `eventos-trabajo`: respuestas de los
  participantes; cada evento se traduce al comando interno ProcesarEventoDeSaga.
"""
from saga.seedwork.aplicacion.comandos import ejecutar_commando
from saga.seedwork.dominio.excepciones import ExcepcionDominio
from saga.seedwork.infraestructura.broker import broker
from ..aplicacion.comandos.iniciar_saga import IniciarSagaAceptacion
from ..aplicacion.comandos.procesar_evento import ProcesarEventoDeSaga

EVENTOS_DE_SAGA = {"CotizacionAceptada", "CotizacionRevertida", "PagoRetenido", "PagoRevertido",
                   "TrabajoAgendado", "TrabajoRechazado"}


def _a_comando(mensaje: dict):
    d = mensaje.get("data", {})
    tipo = mensaje.get("type")
    if tipo == "IniciarSagaAceptacion":
        return IniciarSagaAceptacion(id_mensaje=mensaje["id"], id_cotizacion=d["id_cotizacion"],
                                     id_saga=d.get("id_saga"), datos=d.get("datos", {}))
    if tipo in EVENTOS_DE_SAGA and d.get("id_cotizacion"):
        return ProcesarEventoDeSaga(id_evento=mensaje["id"], tipo_evento=tipo,
                                    id_cotizacion=d["id_cotizacion"], data=d)
    return None


def _handler(app):
    def handler(mensaje):
        comando = _a_comando(mensaje)
        if comando is None:
            return
        with app.test_request_context():
            try:
                ejecutar_commando(comando)
            except ExcepcionDominio as e:
                print(f"[saga] {mensaje.get('type')} RECHAZADO por regla: {e}")
    return handler


def suscribirse_a_comandos(app):
    broker().consumir("comandos-saga", "saga-sub-comandos", _handler(app))


def suscribirse_a_eventos_cotizacion(app):
    broker().consumir("eventos-cotizacion", "saga-sub-eventos-cotizacion", _handler(app))


def suscribirse_a_eventos_pago(app):
    broker().consumir("eventos-pago", "saga-sub-eventos-pago", _handler(app))


def suscribirse_a_eventos_trabajo(app):
    broker().consumir("eventos-trabajo", "saga-sub-eventos-trabajo", _handler(app))
