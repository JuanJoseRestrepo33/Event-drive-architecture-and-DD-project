"""Fábricas para la creación de objetos en la capa de infraestructura"""
from dataclasses import dataclass

from cotizaciones.seedwork.dominio.fabricas import Fabrica
from cotizaciones.seedwork.dominio.repositorios import Repositorio
from ..dominio.repositorios import RepositorioCotizaciones, RepositorioEventosCotizaciones
from .repositorios import (RepositorioCotizacionesSQLAlchemy,
                           RepositorioEventosCotizacionSQLAlchemy)
from .excepciones import ExcepcionFabricaInfraestructura


@dataclass
class FabricaRepositorio(Fabrica):
    def crear_objeto(self, obj: type, mapeador: any = None) -> Repositorio:
        if obj == RepositorioCotizaciones:
            return RepositorioCotizacionesSQLAlchemy()
        elif obj == RepositorioEventosCotizaciones:
            return RepositorioEventosCotizacionSQLAlchemy()
        raise ExcepcionFabricaInfraestructura(f'No existe fábrica para el objeto {obj}')
