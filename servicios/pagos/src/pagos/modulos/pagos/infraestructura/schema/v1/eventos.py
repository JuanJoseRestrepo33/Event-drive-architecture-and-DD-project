"""Evento de INTEGRACIÓN v1 de pagos (contrato público, payload thin, JSON)."""
from dataclasses import dataclass, field

from pagos.seedwork.infraestructura.schema.v1.eventos import EventoIntegracion


@dataclass
class PagoRetenidoPayload:
    id_pago: str = ""
    id_cotizacion: str = ""
    id_trabajo: str = ""
    monto: float = 0.0
    moneda: str = ""
    pais: str = "CO"


@dataclass
class EventoPagoRetenido(EventoIntegracion):
    type: str = "PagoRetenido"
    data: PagoRetenidoPayload = field(default_factory=PagoRetenidoPayload)
