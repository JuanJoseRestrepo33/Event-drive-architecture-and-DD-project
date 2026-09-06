"""Mapeadores de infraestructura:
- MapeadorCotizacionInfra: entidad <-> modelo de BD
- MapeadorEventosCotizacion: evento de DOMINIO -> evento de INTEGRACIÓN v1
"""
import uuid

from cotizaciones.seedwork.dominio.repositorios import Mapeador
from ..dominio.entidades import Cotizacion as CotizacionEntidad, SolicitudDeVisita
from ..dominio.objetos_valor import Dinero, Alcance, Vigencia, Moneda, EstadoCotizacion
from ..dominio.eventos import CotizacionCreada, CotizacionAceptada, VisitaSolicitada
from .dto import Cotizacion as CotizacionDbDTO, VisitaCotizacion
from .schema.v1.eventos import (EventoCotizacionCreada, CotizacionCreadaPayload,
                                EventoCotizacionAceptada, CotizacionAceptadaPayload,
                                EventoVisitaSolicitada, VisitaSolicitadaPayload)


class MapeadorCotizacionInfra(Mapeador):
    def obtener_tipo(self) -> type:
        return CotizacionEntidad.__class__

    def entidad_a_dto(self, entidad: CotizacionEntidad) -> CotizacionDbDTO:
        dto = CotizacionDbDTO(
            id=str(entidad.id), id_trabajo=entidad.id_trabajo,
            id_proveedor=entidad.id_proveedor, monto=entidad.valor.monto,
            moneda=entidad.valor.moneda.value,
            categoria=entidad.alcance.categoria,
            descripcion=entidad.alcance.descripcion,
            vigencia_desde=entidad.vigencia.desde,
            vigencia_hasta=entidad.vigencia.hasta,
            estado=entidad.estado.value,
            fecha_creacion=entidad.fecha_creacion)
        dto.visitas = [VisitaCotizacion(id=str(v.id), id_cotizacion=str(entidad.id),
                                        fecha_propuesta=v.fecha_propuesta,
                                        confirmada=v.confirmada) for v in entidad.visitas]
        return dto

    def dto_a_entidad(self, dto: CotizacionDbDTO) -> CotizacionEntidad:
        entidad = CotizacionEntidad()
        entidad._id = uuid.UUID(dto.id)
        entidad.id_trabajo = dto.id_trabajo
        entidad.id_proveedor = dto.id_proveedor
        entidad.valor = Dinero(monto=dto.monto, moneda=Moneda(dto.moneda))
        entidad.alcance = Alcance(categoria=dto.categoria, descripcion=dto.descripcion)
        entidad.vigencia = Vigencia(desde=dto.vigencia_desde, hasta=dto.vigencia_hasta)
        entidad.estado = EstadoCotizacion(dto.estado)
        for vm in dto.visitas:
            v = SolicitudDeVisita()
            v._id = uuid.UUID(vm.id)
            v.fecha_propuesta = vm.fecha_propuesta
            v.confirmada = vm.confirmada
            entidad.visitas.append(v)
        return entidad


class MapeadorEventosCotizacion(Mapeador):
    """Versiona el evento de dominio como evento de integración (v1)."""
    versions = ('v1',)
    LATEST_VERSION = versions[0]

    def obtener_tipo(self) -> type:
        return CotizacionCreada.__class__

    def es_version_valida(self, version):
        return version in self.versions

    def entidad_a_dto(self, entidad) -> object:
        if not self.es_version_valida(self.LATEST_VERSION):
            raise Exception(f'No existe implementación para la versión {self.LATEST_VERSION}')
        if isinstance(entidad, CotizacionCreada):
            return EventoCotizacionCreada(data=CotizacionCreadaPayload(
                id_cotizacion=str(entidad.id_cotizacion), id_trabajo=entidad.id_trabajo,
                id_proveedor=entidad.id_proveedor, monto=entidad.monto,
                moneda=entidad.moneda))
        if isinstance(entidad, CotizacionAceptada):
            return EventoCotizacionAceptada(data=CotizacionAceptadaPayload(
                id_cotizacion=str(entidad.id_cotizacion), id_trabajo=entidad.id_trabajo,
                id_proveedor=entidad.id_proveedor, monto=entidad.monto,
                moneda=entidad.moneda))
        if isinstance(entidad, VisitaSolicitada):
            return EventoVisitaSolicitada(data=VisitaSolicitadaPayload(
                id_cotizacion=str(entidad.id_cotizacion),
                fecha_propuesta=entidad.fecha_propuesta))
        raise Exception(f'No existe mapeo de integración para {type(entidad).__name__}')

    def dto_a_entidad(self, dto):
        raise NotImplementedError
