from dataclasses import dataclass, field
from notificaciones.seedwork.aplicacion.dto import DTO


@dataclass(frozen=True)
class NotificacionDTO(DTO):
    tipo: str = field(default="")
    version: str = field(default="")
    destinatario: str = field(default="")
    mensaje: str = field(default="")
    estado: str = field(default="")
    id: str = field(default_factory=str)
