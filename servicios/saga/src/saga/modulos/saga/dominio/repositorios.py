"""Puertos de repositorio del orquestador."""
from abc import ABC, abstractmethod

from saga.seedwork.dominio.repositorios import Repositorio


class RepositorioSagas(Repositorio, ABC):
    @abstractmethod
    def obtener_por_cotizacion(self, id_cotizacion: str):
        ...

    @abstractmethod
    def contar_por_estado(self) -> dict:
        ...


class RepositorioSagaLog(ABC):
    """Puerto del SAGA LOG: registro append-only de cada transición."""
    @abstractmethod
    def agregar(self, entrada):
        ...

    @abstractmethod
    def por_saga(self, id_saga: str) -> list:
        ...


class RepositorioEventosProcesados(ABC):
    """Idempotencia del orquestador ante re-entregas del broker."""
    @abstractmethod
    def ya_procesado(self, id_evento: str) -> bool:
        ...

    @abstractmethod
    def agregar(self, id_evento: str):
        ...
