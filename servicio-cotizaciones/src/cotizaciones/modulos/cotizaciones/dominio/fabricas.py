"""Fábricas para la creación de objetos del dominio de cotizaciones"""
from dataclasses import dataclass

from cotizaciones.seedwork.dominio.fabricas import Fabrica
from cotizaciones.seedwork.dominio.repositorios import Mapeador
from cotizaciones.seedwork.dominio.entidades import Entidad
from cotizaciones.seedwork.dominio.eventos import EventoDominio
from .entidades import Cotizacion
from .reglas import MontoDebeSerPositivo, VigenciaDebeSerValida
from .excepciones import TipoObjetoNoExisteEnDominioCotizacionesExcepcion


@dataclass
class _FabricaCotizacion(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        if isinstance(obj, Entidad) or isinstance(obj, EventoDominio):
            return mapeador.entidad_a_dto(obj)
        else:
            cotizacion: Cotizacion = mapeador.dto_a_entidad(obj)
            self.validar_regla(MontoDebeSerPositivo(cotizacion.valor))
            self.validar_regla(VigenciaDebeSerValida(cotizacion.vigencia))
            return cotizacion


@dataclass
class FabricaCotizaciones(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        if mapeador.obtener_tipo() == Cotizacion.__class__:
            fabrica_cotizacion = _FabricaCotizacion()
            return fabrica_cotizacion.crear_objeto(obj, mapeador)
        raise TipoObjetoNoExisteEnDominioCotizacionesExcepcion()
