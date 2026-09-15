"""Base de los eventos de INTEGRACIÓN (contrato público versionado).
Formato alineado a CloudEvents como en el tutorial del curso."""
from dataclasses import dataclass, field
import uuid

from cotizaciones.seedwork.infraestructura.utils import time_millis


@dataclass
class EventoIntegracion:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    time: int = field(default_factory=time_millis)
    ingestion: int = field(default_factory=time_millis)
    specversion: str = field(default='v1')
    type: str = field(default='event')
    datacontenttype: str = field(default='JSON')
    service_name: str = field(default='cotizaciones.hda')
