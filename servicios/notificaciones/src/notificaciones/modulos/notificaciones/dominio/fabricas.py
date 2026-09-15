"""Fábricas del dominio de notificaciones: construyen el agregado validando reglas."""
from dataclasses import dataclass

from notificaciones.seedwork.dominio.fabricas import Fabrica
from notificaciones.seedwork.dominio.repositorios import Mapeador
from notificaciones.seedwork.dominio.entidades import Entidad
from notificaciones.seedwork.dominio.eventos import EventoDominio
from .entidades import Notificacion
from .excepciones import TipoObjetoNoExisteEnDominioNotificacionesExcepcion
from .reglas import DestinatarioObligatorio


@dataclass
class _FabricaNotificacion(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        if isinstance(obj, Entidad) or isinstance(obj, EventoDominio):
            return mapeador.entidad_a_dto(obj)
        entidad: Notificacion = mapeador.dto_a_entidad(obj)
        self.validar_regla(DestinatarioObligatorio(entidad.destinatario))
        return entidad


@dataclass
class FabricaNotificaciones(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        if mapeador.obtener_tipo() == Notificacion.__class__:
            return _FabricaNotificacion().crear_objeto(obj, mapeador)
        raise TipoObjetoNoExisteEnDominioNotificacionesExcepcion()
