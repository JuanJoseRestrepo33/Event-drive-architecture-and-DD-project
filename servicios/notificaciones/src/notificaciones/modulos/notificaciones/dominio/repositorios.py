"""Puertos de repositorio del dominio de notificaciones."""
from abc import ABC, abstractmethod

from notificaciones.seedwork.dominio.repositorios import Repositorio


class RepositorioNotificaciones(Repositorio, ABC):
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
