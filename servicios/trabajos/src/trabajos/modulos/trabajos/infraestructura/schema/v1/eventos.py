"""Evento de INTEGRACIÓN v1 de trabajos (contrato público, payload thin, JSON)."""
from dataclasses import dataclass, field

from trabajos.seedwork.infraestructura.schema.v1.eventos import EventoIntegracion


@dataclass
class TrabajoAgendadoPayload:
    id_agenda: str = ""
    id_trabajo: str = ""
    id_cotizacion: str = ""
    id_pago: str = ""
    pais: str = "CO"


@dataclass
class EventoTrabajoAgendado(EventoIntegracion):
    type: str = "TrabajoAgendado"
    data: TrabajoAgendadoPayload = field(default_factory=TrabajoAgendadoPayload)


@dataclass
class TrabajoRechazadoPayload:
    id_trabajo: str = ""
    id_cotizacion: str = ""
    id_pago: str = ""
    motivo: str = ""


@dataclass
class EventoTrabajoRechazado(EventoIntegracion):
    type: str = "TrabajoRechazado"
    data: TrabajoRechazadoPayload = field(default_factory=TrabajoRechazadoPayload)
