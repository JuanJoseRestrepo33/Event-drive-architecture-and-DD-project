"""Mapeadores de infraestructura: entidad <-> modelo BD; evento dominio -> integración."""
import uuid

from trabajos.seedwork.dominio.repositorios import Mapeador
from ..dominio.entidades import AgendaDeTrabajo
from ..dominio.objetos_valor import Dinero, Moneda, Estado
from .dto import AgendaDeTrabajo as AgendaDeTrabajoDbDTO
from ..dominio.eventos import TrabajoAgendado, TrabajoRechazado
from .schema.v1.eventos import (EventoTrabajoAgendado, TrabajoAgendadoPayload,
                                EventoTrabajoRechazado, TrabajoRechazadoPayload)


class MapeadorAgendaDeTrabajoInfra(Mapeador):
    def obtener_tipo(self) -> type:
        return AgendaDeTrabajo.__class__

    def entidad_a_dto(self, entidad: AgendaDeTrabajo) -> AgendaDeTrabajoDbDTO:
        dto = AgendaDeTrabajoDbDTO()
        dto.id = str(entidad.id)
        dto.estado = entidad.estado.value
        dto.id_trabajo = entidad.id_trabajo
        dto.id_cotizacion = entidad.id_cotizacion
        dto.id_pago = entidad.id_pago
        dto.pais = entidad.pais
        dto.id_proveedor = entidad.id_proveedor
        return dto

    def dto_a_entidad(self, dto: AgendaDeTrabajoDbDTO) -> AgendaDeTrabajo:
        e = AgendaDeTrabajo()
        e._id = uuid.UUID(dto.id)
        e.estado = Estado(dto.estado)
        e.id_trabajo = dto.id_trabajo
        e.id_cotizacion = dto.id_cotizacion
        e.id_pago = dto.id_pago
        e.pais = dto.pais
        e.id_proveedor = dto.id_proveedor
        return e

class MapeadorEventosAgendas(Mapeador):
    """Evento de dominio -> evento de integración v1."""
    def obtener_tipo(self) -> type:
        return TrabajoAgendado.__class__

    def entidad_a_dto(self, evento):
        if isinstance(evento, TrabajoRechazado):
            return EventoTrabajoRechazado(data=TrabajoRechazadoPayload(
                id_trabajo=evento.id_trabajo, id_cotizacion=evento.id_cotizacion,
                id_pago=evento.id_pago, motivo=evento.motivo or ""))
        return EventoTrabajoAgendado(data=TrabajoAgendadoPayload(
            id_agenda=evento.id_agenda, id_trabajo=evento.id_trabajo, id_cotizacion=evento.id_cotizacion,
            id_pago=evento.id_pago, pais=evento.pais))

    def dto_a_entidad(self, dto):
        raise NotImplementedError
