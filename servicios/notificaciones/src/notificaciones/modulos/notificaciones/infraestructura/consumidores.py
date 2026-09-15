"""Consumidores del broker (estilo tutorial). El servicio se suscribe a:
- su tópico de COMANDOS `comandos-notificacion` (comando RegistrarNotificacion directo), y
- los tópicos de EVENTOS de otros servicios, traduciendo cada evento de
  integración al comando de aplicación RegistrarNotificacion (el id del mensaje viaja como
  `id_evento_origen` para la idempotencia).
Cada mensaje se ejecuta con `ejecutar_commando` dentro de un contexto de
request de Flask (la UoW del tutorial vive en la sesión)."""
from notificaciones.seedwork.aplicacion.comandos import ejecutar_commando
from notificaciones.seedwork.dominio.excepciones import ExcepcionDominio
from notificaciones.seedwork.infraestructura.broker import broker
from ..aplicacion.comandos.registrar_notificacion import RegistrarNotificacion


def _a_comando(mensaje: dict):
    d = mensaje.get("data", {})
    tipo = mensaje.get("type")
    v = mensaje.get("specversion", "v1")
    if tipo == "RegistrarNotificacion":
        return RegistrarNotificacion(id_evento_origen=mensaje["id"], tipo=d["tipo"], version=v,
                                     destinatario=d["destinatario"], mensaje=d["mensaje"])
    if tipo == "CotizacionAceptada":
        # consumidor escrito contra v1: si llega v2, el campo 'pais' se ignora (BACKWARD)
        texto = f"Su cotización {d.get('id_cotizacion', '')[:8]}… fue aceptada por {d.get('monto')} {d.get('moneda')}"
        print(f"[notificaciones] CotizacionAceptada {v} recibida"
              f"{' — campo pais ignorado (consumidor v1)' if 'pais' in d else ''}")
        return RegistrarNotificacion(id_evento_origen=mensaje["id"], tipo=tipo, version=v,
                                     destinatario=d.get("id_proveedor", "proveedor"), mensaje=texto)
    if tipo == "PagoRetenido":
        return RegistrarNotificacion(id_evento_origen=mensaje["id"], tipo=tipo, version=v,
                                     destinatario="proveedor",
                                     mensaje=f"Pago de {d.get('monto')} {d.get('moneda')} retenido en escrow")
    if tipo == "TrabajoAgendado":
        return RegistrarNotificacion(id_evento_origen=mensaje["id"], tipo=tipo, version=v,
                                     destinatario="cliente",
                                     mensaje=f"Su trabajo {d.get('id_trabajo')} quedó agendado con pago garantizado")
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
                    print(f"[notificaciones] CONSUMIDO {mensaje.get('type')} {mensaje.get('specversion')} "
                          f"-> RegistrarNotificacion -> {resultado}")
            except ExcepcionDominio as e:
                print(f"[notificaciones] {mensaje.get('type')} RECHAZADO por regla: {e}")
    return handler


def suscribirse_a_comandos(app):
    broker().consumir("comandos-notificacion", "notificaciones-sub-comandos", _handler(app))


def suscribirse_a_eventos_cotizacion(app):
    broker().consumir("eventos-cotizacion", "notificaciones-sub-eventos-cotizacion", _handler(app))


def suscribirse_a_eventos_pago(app):
    broker().consumir("eventos-pago", "notificaciones-sub-eventos-pago", _handler(app))


def suscribirse_a_eventos_trabajo(app):
    broker().consumir("eventos-trabajo", "notificaciones-sub-eventos-trabajo", _handler(app))

