"""Consumidores del broker (estilo tutorial).

ORQUESTACIÓN (Entrega 5): pagos reacciona ÚNICAMENTE a COMANDOS de su tópico
`comandos-pago`, publicados por el orquestador de la saga (o por el BFF para
pruebas): RetenerPago (paso) y RevertirPago (compensación). Ya no traduce
eventos de otros servicios a comandos: la decisión de "qué sigue" vive en
la saga, no en cada consumidor.
Cada mensaje se ejecuta con `ejecutar_commando` dentro de un contexto de
request de Flask (la UoW del tutorial vive en la sesión)."""
from pagos.seedwork.aplicacion.comandos import ejecutar_commando
from pagos.seedwork.dominio.excepciones import ExcepcionDominio
from pagos.seedwork.infraestructura.broker import broker
from ..aplicacion.comandos.retener_pago import RetenerPago
from ..aplicacion.comandos.revertir_pago import RevertirPago


def _a_comando(mensaje: dict):
    d = mensaje.get("data", {})
    tipo = mensaje.get("type")
    if tipo == "RetenerPago":
        return RetenerPago(id_evento_origen=mensaje["id"], id_cotizacion=d["id_cotizacion"],
                           id_trabajo=d["id_trabajo"], monto=d["monto"], moneda=d["moneda"],
                           pais=d.get("pais", "CO"))
    if tipo == "RevertirPago":
        return RevertirPago(id_evento_origen=mensaje["id"], id_cotizacion=d["id_cotizacion"],
                            motivo=d.get("motivo", "compensacion de saga"))
    return None


def _handler(app):
    def handler(mensaje):
        comando = _a_comando(mensaje)
        if comando is None:
            return
        with app.test_request_context():
            try:
                resultado = ejecutar_commando(comando)
                if resultado != "DUPLICADO":
                    print(f"[pagos] CONSUMIDO COMANDO {mensaje.get('type')} -> {resultado}")
            except ExcepcionDominio as e:
                print(f"[pagos] {mensaje.get('type')} RECHAZADO por regla: {e}")
    return handler


def suscribirse_a_comandos(app):
    broker().consumir("comandos-pago", "pagos-sub-comandos", _handler(app))
