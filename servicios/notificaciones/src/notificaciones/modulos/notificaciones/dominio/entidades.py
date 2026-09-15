"""Entidades del dominio de notificaciones. Agregado Notificacion (raíz de agregación):
modelo CRUD — el estado se persiste directamente; las operaciones validan
reglas y agregan eventos de dominio que la UoW publica."""
from dataclasses import dataclass, field

from notificaciones.seedwork.dominio.entidades import AgregacionRaiz
from .objetos_valor import Dinero, Estado
from .eventos import NotificacionRegistrada


@dataclass
class Notificacion(AgregacionRaiz):
    tipo: str = field(default=None)
    version: str = field(default=None)
    destinatario: str = field(default=None)
    mensaje: str = field(default=None)
    estado: Estado = field(default=Estado.ENVIADA)

    def registrar(self):
        self.estado = Estado.ENVIADA
        self.agregar_evento(NotificacionRegistrada(
            id_notificacion=str(self.id), tipo=self.tipo, destinatario=self.destinatario))
