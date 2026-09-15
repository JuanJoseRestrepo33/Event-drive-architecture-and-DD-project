"""Eventos de DOMINIO del módulo de cotizaciones (internos al servicio).
Son también los registros del EVENT STORE: el agregado se reconstruye
aplicándolos en orden (event sourcing)."""
from dataclasses import dataclass
import uuid

from cotizaciones.seedwork.dominio.eventos import EventoDominio


@dataclass
class CotizacionCreada(EventoDominio):
    id_cotizacion: uuid.UUID = None
    id_trabajo: str = None
    id_proveedor: str = None
    monto: float = None
    moneda: str = None
    pais: str = None


@dataclass
class CotizacionAceptada(EventoDominio):
    id_cotizacion: uuid.UUID = None
    id_trabajo: str = None
    id_proveedor: str = None
    monto: float = None
    moneda: str = None
    pais: str = None
