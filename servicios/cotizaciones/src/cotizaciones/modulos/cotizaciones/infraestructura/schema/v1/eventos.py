"""Eventos de INTEGRACIÓN v1 (contrato público, payload thin, JSON)."""
from dataclasses import dataclass, field

from cotizaciones.seedwork.infraestructura.schema.v1.eventos import EventoIntegracion


@dataclass
class CotizacionCreadaPayload:
    id_cotizacion: str = ""
    id_trabajo: str = ""
    id_proveedor: str = ""
    monto: float = 0.0
    moneda: str = ""


@dataclass
class EventoCotizacionCreada(EventoIntegracion):
    type: str = "CotizacionCreada"
    data: CotizacionCreadaPayload = field(default_factory=CotizacionCreadaPayload)


@dataclass
class CotizacionAceptadaPayload:
    id_cotizacion: str = ""
    id_trabajo: str = ""
    id_proveedor: str = ""
    monto: float = 0.0
    moneda: str = ""


@dataclass
class EventoCotizacionAceptada(EventoIntegracion):
    type: str = "CotizacionAceptada"
    data: CotizacionAceptadaPayload = field(default_factory=CotizacionAceptadaPayload)


@dataclass
class CotizacionRevertidaPayload:
    id_cotizacion: str = ""
    id_trabajo: str = ""
    motivo: str = ""


@dataclass
class EventoCotizacionRevertida(EventoIntegracion):
    type: str = "CotizacionRevertida"
    data: CotizacionRevertidaPayload = field(default_factory=CotizacionRevertidaPayload)
