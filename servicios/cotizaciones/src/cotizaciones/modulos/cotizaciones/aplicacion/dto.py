from dataclasses import dataclass, field
from cotizaciones.seedwork.aplicacion.dto import DTO


@dataclass(frozen=True)
class CotizacionDTO(DTO):
    id_trabajo: str = field(default_factory=str)
    id_proveedor: str = field(default_factory=str)
    monto: float = field(default=0.0)
    moneda: str = field(default="COP")
    pais: str = field(default="CO")
    estado: str = field(default="")
    version: int = field(default=0)
    id: str = field(default_factory=str)
