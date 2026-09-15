"""Mapeadores de infraestructura: entidad <-> modelo BD; evento dominio -> integración."""
import uuid

from notificaciones.seedwork.dominio.repositorios import Mapeador
from ..dominio.entidades import Notificacion
from ..dominio.objetos_valor import Dinero, Moneda, Estado
from .dto import Notificacion as NotificacionDbDTO


class MapeadorNotificacionInfra(Mapeador):
    def obtener_tipo(self) -> type:
        return Notificacion.__class__

    def entidad_a_dto(self, entidad: Notificacion) -> NotificacionDbDTO:
        dto = NotificacionDbDTO()
        dto.id = str(entidad.id)
        dto.estado = entidad.estado.value
        dto.tipo = entidad.tipo
        dto.version = entidad.version
        dto.destinatario = entidad.destinatario
        dto.mensaje = entidad.mensaje
        return dto

    def dto_a_entidad(self, dto: NotificacionDbDTO) -> Notificacion:
        e = Notificacion()
        e._id = uuid.UUID(dto.id)
        e.estado = Estado(dto.estado)
        e.tipo = dto.tipo
        e.version = dto.version
        e.destinatario = dto.destinatario
        e.mensaje = dto.mensaje
        return e