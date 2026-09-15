"""Eventos de DOMINIO del módulo de pagos."""
from dataclasses import dataclass

from pagos.seedwork.dominio.eventos import EventoDominio


@dataclass
class PagoRetenido(EventoDominio):
    id_pago: str = None
    id_cotizacion: str = None
    id_trabajo: str = None
    monto: float = None
    moneda: str = None
    pais: str = None
