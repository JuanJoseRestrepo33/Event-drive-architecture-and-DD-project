"""Objetos valor del dominio de cotizaciones"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from cotizaciones.seedwork.dominio.objetos_valor import ObjetoValor


class Moneda(str, Enum):
    COP = "COP"
    MXN = "MXN"
    BRL = "BRL"
    ARS = "ARS"


class EstadoCotizacion(str, Enum):
    EMITIDA = "EMITIDA"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"
    VENCIDA = "VENCIDA"


@dataclass(frozen=True)
class Dinero(ObjetoValor):
    """Multi-moneda desde el diseño: la expansión (MX/BR/AR) es un dato."""
    monto: float
    moneda: Moneda


@dataclass(frozen=True)
class Alcance(ObjetoValor):
    categoria: str
    descripcion: str


@dataclass(frozen=True)
class Vigencia(ObjetoValor):
    desde: datetime
    hasta: datetime

    def vigente(self, momento: datetime) -> bool:
        return self.desde <= momento <= self.hasta
