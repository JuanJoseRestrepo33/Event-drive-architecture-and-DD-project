"""Fábricas del dominio de trabajos: construyen el agregado validando reglas."""
from dataclasses import dataclass

from trabajos.seedwork.dominio.fabricas import Fabrica
from trabajos.seedwork.dominio.repositorios import Mapeador
from trabajos.seedwork.dominio.entidades import Entidad
from trabajos.seedwork.dominio.eventos import EventoDominio
from .entidades import AgendaDeTrabajo
from .excepciones import TipoObjetoNoExisteEnDominioTrabajosExcepcion
from .reglas import DebeExistirPagoRetenido


@dataclass
class _FabricaAgendaDeTrabajo(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        if isinstance(obj, Entidad) or isinstance(obj, EventoDominio):
            return mapeador.entidad_a_dto(obj)
        entidad: AgendaDeTrabajo = mapeador.dto_a_entidad(obj)
        self.validar_regla(DebeExistirPagoRetenido(entidad.id_pago))
        return entidad


@dataclass
class FabricaAgendas(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        if mapeador.obtener_tipo() == AgendaDeTrabajo.__class__:
            return _FabricaAgendaDeTrabajo().crear_objeto(obj, mapeador)
        raise TipoObjetoNoExisteEnDominioTrabajosExcepcion()
