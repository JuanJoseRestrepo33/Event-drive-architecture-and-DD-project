"""Fábricas del dominio de cotizaciones (validan reglas al construir)."""
from dataclasses import dataclass

from cotizaciones.seedwork.dominio.fabricas import Fabrica
from cotizaciones.seedwork.dominio.repositorios import Mapeador
from cotizaciones.seedwork.dominio.entidades import Entidad
from cotizaciones.seedwork.dominio.eventos import EventoDominio
from .entidades import Cotizacion
from .reglas import MontoDebeSerPositivo
from .excepciones import TipoObjetoNoExisteEnDominioCotizacionesExcepcion


@dataclass
class _FabricaCotizacion(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        if isinstance(obj, Entidad) or isinstance(obj, EventoDominio):
            return mapeador.entidad_a_dto(obj)
        cotizacion: Cotizacion = mapeador.dto_a_entidad(obj)
        self.validar_regla(MontoDebeSerPositivo(cotizacion.valor))
        return cotizacion


@dataclass
class FabricaCotizaciones(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        if mapeador.obtener_tipo() == Cotizacion.__class__:
            return _FabricaCotizacion().crear_objeto(obj, mapeador)
        raise TipoObjetoNoExisteEnDominioCotizacionesExcepcion()
