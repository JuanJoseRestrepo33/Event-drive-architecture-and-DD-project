"""Mapeadores de aplicación: DTO <-> entidad."""
from notificaciones.seedwork.aplicacion.dto import Mapeador as AppMap
from notificaciones.seedwork.dominio.repositorios import Mapeador as RepMap
from notificaciones.modulos.notificaciones.dominio.entidades import Notificacion
from notificaciones.modulos.notificaciones.dominio.objetos_valor import Dinero, Moneda
from .dto import NotificacionDTO


class MapeadorNotificacionDTOJson(AppMap):
    def externo_a_dto(self, externo: dict) -> NotificacionDTO:
        return NotificacionDTO(**externo)

    def dto_a_externo(self, dto: NotificacionDTO) -> dict:
        return dto.__dict__


class MapeadorNotificacion(RepMap):
    def obtener_tipo(self) -> type:
        return Notificacion.__class__

    def entidad_a_dto(self, entidad: Notificacion) -> NotificacionDTO:
        return NotificacionDTO(id=str(entidad.id), estado=entidad.estado.value,
            tipo=entidad.tipo, version=entidad.version,
            destinatario=entidad.destinatario, mensaje=entidad.mensaje)

    def dto_a_entidad(self, dto: NotificacionDTO) -> Notificacion:
        entidad = Notificacion()
        entidad.tipo = dto.tipo
        entidad.version = dto.version
        entidad.destinatario = dto.destinatario
        entidad.mensaje = dto.mensaje
        return entidad
