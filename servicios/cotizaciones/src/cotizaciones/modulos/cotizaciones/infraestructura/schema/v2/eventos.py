"""Eventos de INTEGRACIÓN v2: evolución BACKWARD del contrato — SOLO agrega
el campo opcional `pais` (expansión global). Un consumidor v1 procesa v2
ignorando el campo nuevo (escenario E6)."""
from dataclasses import dataclass, field

from cotizaciones.seedwork.infraestructura.schema.v1.eventos import EventoIntegracion


@dataclass
class CotizacionAceptadaPayloadV2:
    id_cotizacion: str = ""
    id_trabajo: str = ""
    id_proveedor: str = ""
    monto: float = 0.0
    moneda: str = ""
    pais: str = "CO"          # NUEVO en v2


@dataclass
class EventoCotizacionAceptadaV2(EventoIntegracion):
    specversion: str = "v2"
    type: str = "CotizacionAceptada"
    data: CotizacionAceptadaPayloadV2 = field(default_factory=CotizacionAceptadaPayloadV2)
