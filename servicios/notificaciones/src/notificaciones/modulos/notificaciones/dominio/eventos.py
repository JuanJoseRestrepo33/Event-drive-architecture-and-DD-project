"""Eventos de DOMINIO del módulo de notificaciones."""
from dataclasses import dataclass

from notificaciones.seedwork.dominio.eventos import EventoDominio


@dataclass
class NotificacionRegistrada(EventoDominio):
    id_notificacion: str = None
    tipo: str = None
    destinatario: str = None
