"""Cableado de señales (pydispatch) del módulo."""
from pydispatch import dispatcher

from .handlers import HandlerNotificacionIntegracion
from notificaciones.modulos.notificaciones.dominio.eventos import NotificacionRegistrada

dispatcher.connect(HandlerNotificacionIntegracion.handle_notificacion_registrada,
                   signal=f'{NotificacionRegistrada.__name__}Integracion')
