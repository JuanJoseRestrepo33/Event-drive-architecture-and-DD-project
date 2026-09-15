from dataclasses import dataclass

from pagos.seedwork.dominio.fabricas import Fabrica
from ..dominio.repositorios import RepositorioReservas, RepositorioEventosProcesados
from .repositorios import RepositorioReservasSQLAlchemy, RepositorioEventosProcesadosSQLAlchemy
from .excepciones import ExcepcionFabricaInfraestructura


@dataclass
class FabricaRepositorio(Fabrica):
    def crear_objeto(self, obj: type, mapeador: any = None):
        if obj == RepositorioReservas:
            return RepositorioReservasSQLAlchemy()
        elif obj == RepositorioEventosProcesados:
            return RepositorioEventosProcesadosSQLAlchemy()
        raise ExcepcionFabricaInfraestructura(f'No existe fábrica para el objeto {obj}')
