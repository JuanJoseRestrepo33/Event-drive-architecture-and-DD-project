from dataclasses import dataclass

from trabajos.seedwork.dominio.fabricas import Fabrica
from ..dominio.repositorios import RepositorioAgendas, RepositorioEventosProcesados
from .repositorios import RepositorioAgendasSQLAlchemy, RepositorioEventosProcesadosSQLAlchemy
from .excepciones import ExcepcionFabricaInfraestructura


@dataclass
class FabricaRepositorio(Fabrica):
    def crear_objeto(self, obj: type, mapeador: any = None):
        if obj == RepositorioAgendas:
            return RepositorioAgendasSQLAlchemy()
        elif obj == RepositorioEventosProcesados:
            return RepositorioEventosProcesadosSQLAlchemy()
        raise ExcepcionFabricaInfraestructura(f'No existe fábrica para el objeto {obj}')
