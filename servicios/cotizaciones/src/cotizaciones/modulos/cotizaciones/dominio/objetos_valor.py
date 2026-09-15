"""Objetos valor del dominio de cotizaciones (inmutables, sin identidad)."""
from dataclasses import dataclass
from enum import Enum

from cotizaciones.seedwork.dominio.objetos_valor import ObjetoValor


class Moneda(str, Enum):
    COP = "COP"
    MXN = "MXN"
    BRL = "BRL"
    ARS = "ARS"          # expansión global: multi-moneda por diseño


class EstadoCotizacion(str, Enum):
    EMITIDA = "EMITIDA"
    ACEPTADA = "ACEPTADA"


@dataclass(frozen=True)
class Dinero(ObjetoValor):
    monto: float
    moneda: Moneda
