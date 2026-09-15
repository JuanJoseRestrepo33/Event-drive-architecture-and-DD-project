"""Handlers de aplicación de notificaciones: el evento de dominio NotificacionRegistrada es interno
(no se publica al broker: notificaciones es un consumidor final)."""
from notificaciones.seedwork.aplicacion.handlers import Handler


class HandlerNotificacionIntegracion(Handler):
    @staticmethod
    def handle_notificacion_registrada(evento):
        print(f"[notificaciones] NotificacionRegistrada (evento de dominio interno) -> {evento.destinatario}")
