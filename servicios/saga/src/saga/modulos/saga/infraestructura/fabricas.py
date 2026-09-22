from dataclasses import dataclass

from saga.seedwork.dominio.fabricas import Fabrica
from saga.seedwork.dominio.excepciones import ExcepcionFabrica
from ..dominio.repositorios import RepositorioSagas, RepositorioSagaLog, RepositorioEventosProcesados
from .repositorios import (RepositorioSagasSQLAlchemy, RepositorioSagaLogSQLAlchemy,
                           RepositorioEventosProcesadosSQLAlchemy)


@dataclass
class FabricaRepositorio(Fabrica):
    def crear_objeto(self, obj: type, mapeador: any = None):
        if obj == RepositorioSagas:
            return RepositorioSagasSQLAlchemy()
        if obj == RepositorioSagaLog:
            return RepositorioSagaLogSQLAlchemy()
        if obj == RepositorioEventosProcesados:
            return RepositorioEventosProcesadosSQLAlchemy()
        raise ExcepcionFabrica(f"No existe fábrica para {obj}")
