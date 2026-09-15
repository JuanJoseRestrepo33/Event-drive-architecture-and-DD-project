"""Puertos de repositorio del dominio de cotizaciones."""
from abc import ABC, abstractmethod
from uuid import UUID

from cotizaciones.seedwork.dominio.repositorios import Repositorio


class RepositorioCotizaciones(Repositorio, ABC):
    """PROYECCIÓN (read model) del agregado, para las consultas (lado Q)."""
    @abstractmethod
    def obtener_por_trabajo(self, id_trabajo: str) -> list:
        ...


class RepositorioEventosCotizaciones(Repositorio, ABC):
    """EVENT STORE (event sourcing): fuente de verdad, append-only."""
    @abstractmethod
    def reconstruir(self, id: UUID):
        """Reconstruye el agregado aplicando su historia de eventos."""
        ...
