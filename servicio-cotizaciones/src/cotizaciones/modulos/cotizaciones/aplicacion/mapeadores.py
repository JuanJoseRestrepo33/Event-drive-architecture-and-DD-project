"""Mapeadores de la capa de aplicación:
- MapeadorCotizacionDTOJson: mundo externo (JSON) <-> DTO
- MapeadorCotizacion: DTO <-> entidad del dominio (usado por la fábrica)
"""
from datetime import datetime

from cotizaciones.seedwork.aplicacion.dto import Mapeador as AppMap
from cotizaciones.seedwork.dominio.repositorios import Mapeador
from ..dominio.entidades import Cotizacion
from ..dominio.objetos_valor import Dinero, Alcance, Vigencia, Moneda
from .dto import CotizacionDTO, VisitaDTO


class MapeadorCotizacionDTOJson(AppMap):
    def externo_a_dto(self, externo: dict) -> CotizacionDTO:
        return CotizacionDTO(
            id_trabajo=externo.get('id_trabajo'),
            id_proveedor=externo.get('id_proveedor'),
            monto=externo.get('monto'),
            moneda=externo.get('moneda', 'COP'),
            categoria=externo.get('categoria', ''),
            descripcion=externo.get('descripcion', ''),
            vigencia_desde=externo.get('vigencia_desde'),
            vigencia_hasta=externo.get('vigencia_hasta'))

    def dto_a_externo(self, dto: CotizacionDTO) -> dict:
        return dto.__dict__ | {
            'visitas': [v.__dict__ for v in dto.visitas]}


class MapeadorCotizacion(Mapeador):
    def obtener_tipo(self) -> type:
        return Cotizacion.__class__

    def entidad_a_dto(self, entidad: Cotizacion) -> CotizacionDTO:
        return CotizacionDTO(
            id=str(entidad.id), id_trabajo=entidad.id_trabajo,
            id_proveedor=entidad.id_proveedor, monto=entidad.valor.monto,
            moneda=entidad.valor.moneda.value,
            categoria=entidad.alcance.categoria,
            descripcion=entidad.alcance.descripcion,
            vigencia_desde=entidad.vigencia.desde.isoformat(),
            vigencia_hasta=entidad.vigencia.hasta.isoformat(),
            estado=entidad.estado.value,
            visitas=[VisitaDTO(fecha_propuesta=v.fecha_propuesta.isoformat(),
                               confirmada=v.confirmada) for v in entidad.visitas])

    def dto_a_entidad(self, dto: CotizacionDTO) -> Cotizacion:
        cotizacion = Cotizacion()
        cotizacion.id_trabajo = dto.id_trabajo
        cotizacion.id_proveedor = dto.id_proveedor
        cotizacion.valor = Dinero(monto=float(dto.monto), moneda=Moneda(dto.moneda))
        cotizacion.alcance = Alcance(categoria=dto.categoria, descripcion=dto.descripcion)
        cotizacion.vigencia = Vigencia(
            desde=datetime.fromisoformat(dto.vigencia_desde),
            hasta=datetime.fromisoformat(dto.vigencia_hasta))
        return cotizacion
