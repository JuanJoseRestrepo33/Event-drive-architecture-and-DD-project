"""Consumidores del broker (estilo tutorial). El servicio se suscribe a:
- su tópico de COMANDOS `comandos-trabajo` (comando AgendarTrabajo directo), y
- los tópicos de EVENTOS de otros servicios, traduciendo cada evento de
  integración al comando de aplicación AgendarTrabajo (el id del mensaje viaja como
  `id_evento_origen` para la idempotencia).
Cada mensaje se ejecuta con `ejecutar_commando` dentro de un contexto de
request de Flask (la UoW del tutorial vive en la sesión)."""
from trabajos.seedwork.aplicacion.comandos import ejecutar_commando
from trabajos.seedwork.dominio.excepciones import ExcepcionDominio
from trabajos.seedwork.infraestructura.broker import broker
from ..aplicacion.comandos.agendar_trabajo import AgendarTrabajo


def _a_comando(mensaje: dict):
    d = mensaje.get("data", {})
    tipo = mensaje.get("type")
    if tipo == "AgendarTrabajo" or tipo == "PagoRetenido":
        return AgendarTrabajo(id_evento_origen=mensaje["id"], id_trabajo=d["id_trabajo"],
                              id_cotizacion=d["id_cotizacion"], id_pago=d["id_pago"],
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
                    print(f"[trabajos] CONSUMIDO {mensaje.get('type')} {mensaje.get('specversion')} "
                          f"-> AgendarTrabajo -> {resultado}")
            except ExcepcionDominio as e:
                print(f"[trabajos] {mensaje.get('type')} RECHAZADO por regla: {e}")
    return handler


def suscribirse_a_comandos(app):
    broker().consumir("comandos-trabajo", "trabajos-sub-comandos", _handler(app))


def suscribirse_a_eventos_pago(app):
    broker().consumir("eventos-pago", "trabajos-sub-eventos-pago", _handler(app))

