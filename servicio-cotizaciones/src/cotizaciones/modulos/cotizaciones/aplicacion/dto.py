"""DTOs de la capa de aplicación del dominio de cotizaciones"""
from dataclasses import dataclass, field

from cotizaciones.seedwork.aplicacion.dto import DTO


@dataclass(frozen=True)
class VisitaDTO(DTO):
    fecha_propuesta: str = ""
    confirmada: bool = False


@dataclass(frozen=True)
class CotizacionDTO(DTO):
    id: str = ""
    id_trabajo: str = ""
    id_proveedor: str = ""
    monto: float = 0.0
    moneda: str = "COP"
    categoria: str = ""
    descripcion: str = ""
    vigencia_desde: str = ""
    vigencia_hasta: str = ""
    estado: str = ""
    visitas: list[VisitaDTO] = field(default_factory=list)
