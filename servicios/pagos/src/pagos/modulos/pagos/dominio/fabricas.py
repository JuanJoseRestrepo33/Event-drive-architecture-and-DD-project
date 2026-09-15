"""Fábricas del dominio de pagos: construyen el agregado validando reglas."""
from dataclasses import dataclass

from pagos.seedwork.dominio.fabricas import Fabrica
from pagos.seedwork.dominio.repositorios import Mapeador
from pagos.seedwork.dominio.entidades import Entidad
from pagos.seedwork.dominio.eventos import EventoDominio
from .entidades import ReservaDePago
from .excepciones import TipoObjetoNoExisteEnDominioPagosExcepcion
from .reglas import MontoDebeSerPositivo


@dataclass
class _FabricaReservaDePago(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        if isinstance(obj, Entidad) or isinstance(obj, EventoDominio):
            return mapeador.entidad_a_dto(obj)
        entidad: ReservaDePago = mapeador.dto_a_entidad(obj)
        self.validar_regla(MontoDebeSerPositivo(entidad.valor))
        return entidad


@dataclass
class FabricaReservas(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        if mapeador.obtener_tipo() == ReservaDePago.__class__:
            return _FabricaReservaDePago().crear_objeto(obj, mapeador)
        raise TipoObjetoNoExisteEnDominioPagosExcepcion()
