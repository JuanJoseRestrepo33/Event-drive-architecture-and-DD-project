from dataclasses import dataclass, field
import uuid

from cotizaciones.seedwork.infraestructura.utils import time_millis


@dataclass
class ComandoIntegracion:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    time: int = field(default_factory=time_millis)
    specversion: str = field(default='v1')
    type: str = field(default='command')
    datacontenttype: str = field(default='JSON')
    service_name: str = field(default='cotizaciones.hda')
