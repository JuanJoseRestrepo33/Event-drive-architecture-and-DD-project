"""Mapeadores de aplicación: DTO <-> entidad."""
from trabajos.seedwork.aplicacion.dto import Mapeador as AppMap
from trabajos.seedwork.dominio.repositorios import Mapeador as RepMap
from trabajos.modulos.trabajos.dominio.entidades import AgendaDeTrabajo
from trabajos.modulos.trabajos.dominio.objetos_valor import Dinero, Moneda
from .dto import AgendaDeTrabajoDTO


class MapeadorAgendaDeTrabajoDTOJson(AppMap):
    def externo_a_dto(self, externo: dict) -> AgendaDeTrabajoDTO:
        return AgendaDeTrabajoDTO(**externo)

    def dto_a_externo(self, dto: AgendaDeTrabajoDTO) -> dict:
        return dto.__dict__


class MapeadorAgendaDeTrabajo(RepMap):
    def obtener_tipo(self) -> type:
        return AgendaDeTrabajo.__class__

    def entidad_a_dto(self, entidad: AgendaDeTrabajo) -> AgendaDeTrabajoDTO:
        return AgendaDeTrabajoDTO(id=str(entidad.id), estado=entidad.estado.value,
            id_trabajo=entidad.id_trabajo, id_cotizacion=entidad.id_cotizacion,
            id_pago=entidad.id_pago, pais=entidad.pais, id_proveedor=entidad.id_proveedor or "")

    def dto_a_entidad(self, dto: AgendaDeTrabajoDTO) -> AgendaDeTrabajo:
        entidad = AgendaDeTrabajo()
        entidad.id_trabajo = dto.id_trabajo
        entidad.id_cotizacion = dto.id_cotizacion
        entidad.id_pago = dto.id_pago
        entidad.pais = dto.pais or "CO"
        entidad.id_proveedor = dto.id_proveedor
        return entidad
