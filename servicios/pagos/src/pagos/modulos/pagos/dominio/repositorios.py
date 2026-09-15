"""Puertos de repositorio del dominio de pagos."""
from abc import ABC, abstractmethod

from pagos.seedwork.dominio.repositorios import Repositorio


class RepositorioReservas(Repositorio, ABC):
    @abstractmethod
    def contar(self) -> int:
        ...


class RepositorioEventosProcesados(ABC):
    """Puerto de IDEMPOTENCIA: registra los ids de mensajes ya consumidos
    para que una re-entrega del broker (at-least-once) no duplique efectos."""
    @abstractmethod
    def ya_procesado(self, id_evento: str) -> bool:
        ...

    @abstractmethod
    def agregar(self, id_evento: str):
        ...
