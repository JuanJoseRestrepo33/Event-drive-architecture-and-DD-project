"""Objetos valor del dominio de trabajos."""
from dataclasses import dataclass
from enum import Enum

from trabajos.seedwork.dominio.objetos_valor import ObjetoValor


class Moneda(str, Enum):
    COP = "COP"
    MXN = "MXN"
    BRL = "BRL"
    ARS = "ARS"


@dataclass(frozen=True)
class Dinero(ObjetoValor):
    monto: float
    moneda: Moneda


class Estado(str, Enum):
    AGENDADO = "AGENDADO"
