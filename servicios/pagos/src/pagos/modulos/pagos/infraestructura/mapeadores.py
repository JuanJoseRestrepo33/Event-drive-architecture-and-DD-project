"""Mapeadores de infraestructura: entidad <-> modelo BD; evento dominio -> integración."""
import uuid

from pagos.seedwork.dominio.repositorios import Mapeador
from ..dominio.entidades import ReservaDePago
from ..dominio.objetos_valor import Dinero, Moneda, Estado
from .dto import ReservaDePago as ReservaDePagoDbDTO
from ..dominio.eventos import PagoRetenido, PagoRevertido
from .schema.v1.eventos import (EventoPagoRetenido, PagoRetenidoPayload,
                                EventoPagoRevertido, PagoRevertidoPayload)


class MapeadorReservaDePagoInfra(Mapeador):
    def obtener_tipo(self) -> type:
        return ReservaDePago.__class__

    def entidad_a_dto(self, entidad: ReservaDePago) -> ReservaDePagoDbDTO:
        dto = ReservaDePagoDbDTO()
        dto.id = str(entidad.id)
        dto.estado = entidad.estado.value
        dto.id_cotizacion = entidad.id_cotizacion
        dto.id_trabajo = entidad.id_trabajo
        dto.monto = entidad.valor.monto
        dto.moneda = entidad.valor.moneda.value
        dto.pais = entidad.pais
        return dto

    def dto_a_entidad(self, dto: ReservaDePagoDbDTO) -> ReservaDePago:
        e = ReservaDePago()
        e._id = uuid.UUID(dto.id)
        e.estado = Estado(dto.estado)
        e.id_cotizacion = dto.id_cotizacion
        e.id_trabajo = dto.id_trabajo
        e.valor = Dinero(dto.monto, Moneda(dto.moneda))
        e.pais = dto.pais
        return e

class MapeadorEventosReservas(Mapeador):
    """Evento de dominio -> evento de integración v1."""
    def obtener_tipo(self) -> type:
        return PagoRetenido.__class__

    def entidad_a_dto(self, evento):
        if isinstance(evento, PagoRevertido):
            return EventoPagoRevertido(data=PagoRevertidoPayload(
                id_pago=evento.id_pago, id_cotizacion=evento.id_cotizacion, id_trabajo=evento.id_trabajo,
                monto=evento.monto, moneda=evento.moneda, motivo=evento.motivo or ""))
        return EventoPagoRetenido(data=PagoRetenidoPayload(
            id_pago=evento.id_pago, id_cotizacion=evento.id_cotizacion, id_trabajo=evento.id_trabajo,
            monto=evento.monto, moneda=evento.moneda, pais=evento.pais))

    def dto_a_entidad(self, dto):
        raise NotImplementedError
