"""Mapeadores de la capa de aplicación: DTO <-> entidad."""
from cotizaciones.seedwork.aplicacion.dto import Mapeador as AppMap
from cotizaciones.seedwork.dominio.repositorios import Mapeador as RepMap
from cotizaciones.modulos.cotizaciones.dominio.entidades import Cotizacion
from cotizaciones.modulos.cotizaciones.dominio.objetos_valor import Dinero, Moneda
from .dto import CotizacionDTO


class MapeadorCotizacionDTOJson(AppMap):
    def externo_a_dto(self, externo: dict) -> CotizacionDTO:
        return CotizacionDTO(**externo)

    def dto_a_externo(self, dto: CotizacionDTO) -> dict:
        return dto.__dict__


class MapeadorCotizacion(RepMap):
    def obtener_tipo(self) -> type:
        return Cotizacion.__class__

    def entidad_a_dto(self, entidad: Cotizacion) -> CotizacionDTO:
        return CotizacionDTO(
            id=str(entidad.id), id_trabajo=entidad.id_trabajo, id_proveedor=entidad.id_proveedor,
            monto=entidad.valor.monto, moneda=entidad.valor.moneda.value, pais=entidad.pais,
            estado=entidad.estado.value if entidad.estado else "", version=entidad.version)

    def dto_a_entidad(self, dto: CotizacionDTO) -> Cotizacion:
        cotizacion = Cotizacion()
        cotizacion.id_trabajo = dto.id_trabajo
        cotizacion.id_proveedor = dto.id_proveedor
        cotizacion.valor = Dinero(float(dto.monto), Moneda(dto.moneda))
        cotizacion.pais = dto.pais or "CO"
        return cotizacion
