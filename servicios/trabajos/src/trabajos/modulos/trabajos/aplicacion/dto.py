from dataclasses import dataclass, field
from trabajos.seedwork.aplicacion.dto import DTO


@dataclass(frozen=True)
class AgendaDeTrabajoDTO(DTO):
    id_trabajo: str = field(default="")
    id_cotizacion: str = field(default="")
    id_pago: str = field(default="")
    pais: str = field(default="CO")
    id_proveedor: str = field(default="")
    estado: str = field(default="")
    id: str = field(default_factory=str)
