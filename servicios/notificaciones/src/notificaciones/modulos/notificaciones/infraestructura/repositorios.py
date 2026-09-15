"""Repositorios (ADAPTADORES) sobre Flask-SQLAlchemy — modelo CRUD."""
from uuid import UUID

from notificaciones.config.db import db
from ..dominio.repositorios import RepositorioNotificaciones, RepositorioEventosProcesados
from ..dominio.fabricas import FabricaNotificaciones
from .dto import Notificacion as NotificacionDbDTO, EventoProcesado
from .mapeadores import MapeadorNotificacionInfra


class RepositorioNotificacionesSQLAlchemy(RepositorioNotificaciones):

    def __init__(self):
        self._fabrica: FabricaNotificaciones = FabricaNotificaciones()

    def obtener_por_id(self, id: UUID):
        dto = db.session.query(NotificacionDbDTO).filter_by(id=str(id)).one_or_none()
        return None if dto is None else self._fabrica.crear_objeto(dto, MapeadorNotificacionInfra())

    def obtener_todos(self) -> list:
        m = MapeadorNotificacionInfra()
        return [self._fabrica.crear_objeto(d, m) for d in db.session.query(NotificacionDbDTO).all()]

    def contar(self) -> int:
        return db.session.query(NotificacionDbDTO).count()

    def agregar(self, entidad):
        db.session.add(self._fabrica.crear_objeto(entidad, MapeadorNotificacionInfra()))

    def actualizar(self, entidad):
        db.session.merge(self._fabrica.crear_objeto(entidad, MapeadorNotificacionInfra()))

    def eliminar(self, entidad_id):
        db.session.query(NotificacionDbDTO).filter_by(id=str(entidad_id)).delete()


class RepositorioEventosProcesadosSQLAlchemy(RepositorioEventosProcesados):
    def ya_procesado(self, id_evento: str) -> bool:
        return db.session.query(EventoProcesado).filter_by(id_evento=id_evento).one_or_none() is not None

    def agregar(self, id_evento: str):
        db.session.add(EventoProcesado(id_evento=id_evento))
