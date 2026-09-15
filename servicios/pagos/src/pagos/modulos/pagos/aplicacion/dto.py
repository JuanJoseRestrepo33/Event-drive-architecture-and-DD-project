from dataclasses import dataclass, field
from pagos.seedwork.aplicacion.dto import DTO


@dataclass(frozen=True)
class ReservaDePagoDTO(DTO):
    id_cotizacion: str = field(default="")
    id_trabajo: str = field(default="")
    monto: float = field(default=0.0)
    moneda: str = field(default="COP")
    pais: str = field(default="CO")
    estado: str = field(default="")
    id: str = field(default_factory=str)
