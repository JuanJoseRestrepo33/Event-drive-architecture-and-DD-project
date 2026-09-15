"""Mapeadores de aplicación: DTO <-> entidad."""
from pagos.seedwork.aplicacion.dto import Mapeador as AppMap
from pagos.seedwork.dominio.repositorios import Mapeador as RepMap
from pagos.modulos.pagos.dominio.entidades import ReservaDePago
from pagos.modulos.pagos.dominio.objetos_valor import Dinero, Moneda
from .dto import ReservaDePagoDTO


class MapeadorReservaDePagoDTOJson(AppMap):
    def externo_a_dto(self, externo: dict) -> ReservaDePagoDTO:
        return ReservaDePagoDTO(**externo)

    def dto_a_externo(self, dto: ReservaDePagoDTO) -> dict:
        return dto.__dict__


class MapeadorReservaDePago(RepMap):
    def obtener_tipo(self) -> type:
        return ReservaDePago.__class__

    def entidad_a_dto(self, entidad: ReservaDePago) -> ReservaDePagoDTO:
        return ReservaDePagoDTO(id=str(entidad.id), estado=entidad.estado.value,
            id_cotizacion=entidad.id_cotizacion, id_trabajo=entidad.id_trabajo,
            monto=entidad.valor.monto, moneda=entidad.valor.moneda.value, pais=entidad.pais)

    def dto_a_entidad(self, dto: ReservaDePagoDTO) -> ReservaDePago:
        entidad = ReservaDePago()
        entidad.id_cotizacion = dto.id_cotizacion
        entidad.id_trabajo = dto.id_trabajo
        entidad.valor = Dinero(float(dto.monto), Moneda(dto.moneda))
        entidad.pais = dto.pais or "CO"
        return entidad
