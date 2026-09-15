"""Mapeadores de infraestructura: entidad <-> modelo BD (proyección) y
evento de dominio -> evento de integración versionado."""
import uuid

from cotizaciones.seedwork.dominio.repositorios import Mapeador
from ..dominio.entidades import Cotizacion
from ..dominio.eventos import CotizacionCreada, CotizacionAceptada
from ..dominio.objetos_valor import Dinero, Moneda, EstadoCotizacion
from .dto import Cotizacion as CotizacionDbDTO
from .schema.v1.eventos import EventoCotizacionCreada, CotizacionCreadaPayload
from .schema.v2.eventos import EventoCotizacionAceptadaV2, CotizacionAceptadaPayloadV2


class MapeadorCotizacionInfra(Mapeador):
    def obtener_tipo(self) -> type:
        return Cotizacion.__class__

    def entidad_a_dto(self, entidad: Cotizacion) -> CotizacionDbDTO:
        dto = CotizacionDbDTO()
        dto.id = str(entidad.id)
        dto.id_trabajo = entidad.id_trabajo
        dto.id_proveedor = entidad.id_proveedor
        dto.monto = entidad.valor.monto
        dto.moneda = entidad.valor.moneda.value
        dto.pais = entidad.pais
        dto.estado = entidad.estado.value
        dto.version = entidad.version
        return dto

    def dto_a_entidad(self, dto: CotizacionDbDTO) -> Cotizacion:
        c = Cotizacion()
        c._id = uuid.UUID(dto.id)
        c.id_trabajo = dto.id_trabajo
        c.id_proveedor = dto.id_proveedor
        c.valor = Dinero(dto.monto, Moneda(dto.moneda))
        c.pais = dto.pais
        c.estado = EstadoCotizacion(dto.estado)
        c.version = dto.version
        return c


class MapeadorEventosCotizacion(Mapeador):
    """Dominio -> integración. CotizacionCreada se publica como v1;
    CotizacionAceptada como v2 (contrato evolucionado con `pais`)."""
    LATEST_VERSION = 'v2'

    def __init__(self):
        self.router = {CotizacionCreada: self._creada_a_integracion,
                       CotizacionAceptada: self._aceptada_a_integracion}

    def obtener_tipo(self) -> type:
        return CotizacionCreada.__class__

    def es_version_valida(self, version):
        return version in ('v1', 'v2')

    def _creada_a_integracion(self, evento: CotizacionCreada) -> EventoCotizacionCreada:
        return EventoCotizacionCreada(data=CotizacionCreadaPayload(
            id_cotizacion=str(evento.id_cotizacion), id_trabajo=evento.id_trabajo,
            id_proveedor=evento.id_proveedor, monto=evento.monto, moneda=evento.moneda))

    def _aceptada_a_integracion(self, evento: CotizacionAceptada) -> EventoCotizacionAceptadaV2:
        return EventoCotizacionAceptadaV2(data=CotizacionAceptadaPayloadV2(
            id_cotizacion=str(evento.id_cotizacion), id_trabajo=evento.id_trabajo,
            id_proveedor=evento.id_proveedor, monto=evento.monto, moneda=evento.moneda,
            pais=evento.pais or "CO"))

    def entidad_a_dto(self, entidad, version=LATEST_VERSION):
        func = self.router.get(type(entidad))
        if not func:
            raise NotImplementedError(f'No existe mapeo para {type(entidad).__name__}')
        return func(entidad)

    def dto_a_entidad(self, dto, version=LATEST_VERSION):
        raise NotImplementedError
