"""Interfaces (puertos) de los repositorios del dominio de cotizaciones"""
from abc import ABC, abstractmethod

from cotizaciones.seedwork.dominio.repositorios import Repositorio


class RepositorioCotizaciones(Repositorio, ABC):
    @abstractmethod
    def obtener_por_trabajo(self, id_trabajo: str) -> list:
        ...


class RepositorioEventosCotizaciones(Repositorio, ABC):
    """Puerto del event store (event sourcing, tutorial 7): cada evento de
    dominio del agregado se persiste como registro histórico versionado."""
