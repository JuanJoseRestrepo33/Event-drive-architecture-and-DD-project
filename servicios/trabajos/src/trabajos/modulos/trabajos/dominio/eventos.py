"""Eventos de DOMINIO del módulo de trabajos."""
from dataclasses import dataclass

from trabajos.seedwork.dominio.eventos import EventoDominio


@dataclass
class TrabajoAgendado(EventoDominio):
    id_agenda: str = None
    id_trabajo: str = None
    id_cotizacion: str = None
    id_pago: str = None
    pais: str = None
