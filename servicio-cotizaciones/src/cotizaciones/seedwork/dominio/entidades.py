"""Entidades reusables parte del seedwork del proyecto"""
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .eventos import EventoDominio
from .mixins import ValidarReglasMixin
from .reglas import IdEntidadEsInmutable
from .excepciones import IdDebeSerInmutableExcepcion


@dataclass
class Entidad:
    id: uuid.UUID = field(hash=True, default=None)
    _id: uuid.UUID = field(init=False, repr=False, hash=True, default=None)
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: datetime = field(default_factory=datetime.now)

    @classmethod
    def siguiente_id(cls) -> uuid.UUID:
        return uuid.uuid4()

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id: uuid.UUID) -> None:
        if not IdEntidadEsInmutable(self).es_valido():
            raise IdDebeSerInmutableExcepcion()
        self._id = self.siguiente_id()


@dataclass
class AgregacionRaiz(Entidad, ValidarReglasMixin):
    """Raíz de agregación: acumula eventos de dominio (y sus compensaciones)
    que la Unidad de Trabajo publica como señales al registrar el batch
    (señal `XDominio`) y tras el commit (señal `XIntegracion`)."""
    eventos: list[EventoDominio] = field(default_factory=list)
    eventos_compensacion: list[EventoDominio] = field(default_factory=list)

    def agregar_evento(self, evento: EventoDominio, evento_compensacion: EventoDominio = None):
        self.eventos.append(evento)
        if evento_compensacion:
            self.eventos_compensacion.append(evento_compensacion)

    def limpiar_eventos(self):
        self.eventos = list()
        self.eventos_compensacion = list()
