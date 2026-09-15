"""Eventos reusables parte del seedwork del proyecto"""
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .reglas import IdEntidadEsInmutable
from .excepciones import IdDebeSerInmutableExcepcion


@dataclass
class EventoDominio():
    id: uuid.UUID = field(hash=True, default=None)
    _id: uuid.UUID = field(init=False, repr=False, hash=True, default=None)
    fecha_evento: datetime = field(default_factory=datetime.now)

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
