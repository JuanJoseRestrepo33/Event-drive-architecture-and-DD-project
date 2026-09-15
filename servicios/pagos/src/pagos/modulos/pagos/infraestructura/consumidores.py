"""Consumidores del broker (estilo tutorial). El servicio se suscribe a:
- su tópico de COMANDOS `comandos-pago` (comando RetenerPago directo), y
- los tópicos de EVENTOS de otros servicios, traduciendo cada evento de
  integración al comando de aplicación RetenerPago (el id del mensaje viaja como
  `id_evento_origen` para la idempotencia).
Cada mensaje se ejecuta con `ejecutar_commando` dentro de un contexto de
request de Flask (la UoW del tutorial vive en la sesión)."""
from pagos.seedwork.aplicacion.comandos import ejecutar_commando
from pagos.seedwork.dominio.excepciones import ExcepcionDominio
from pagos.seedwork.infraestructura.broker import broker
from ..aplicacion.comandos.retener_pago import RetenerPago


def _a_comando(mensaje: dict):
    d = mensaje.get("data", {})
    tipo = mensaje.get("type")
    if tipo == "RetenerPago" or tipo == "CotizacionAceptada":
        # CotizacionAceptada v1 no trae 'pais' (consumidor tolerante: default CO)
        return RetenerPago(id_evento_origen=mensaje["id"], id_cotizacion=d["id_cotizacion"],
                           id_trabajo=d["id_trabajo"], monto=d["monto"], moneda=d["moneda"],
                           pais=d.get("pais", "CO"))
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
                    print(f"[pagos] CONSUMIDO {mensaje.get('type')} {mensaje.get('specversion')} "
                          f"-> RetenerPago -> {resultado}")
            except ExcepcionDominio as e:
                print(f"[pagos] {mensaje.get('type')} RECHAZADO por regla: {e}")
    return handler


def suscribirse_a_comandos(app):
    broker().consumir("comandos-pago", "pagos-sub-comandos", _handler(app))


def suscribirse_a_eventos_cotizacion(app):
    broker().consumir("eventos-cotizacion", "pagos-sub-eventos-cotizacion", _handler(app))

