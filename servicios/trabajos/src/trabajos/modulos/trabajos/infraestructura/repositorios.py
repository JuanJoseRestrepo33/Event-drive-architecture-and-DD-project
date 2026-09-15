"""Repositorios (ADAPTADORES) sobre Flask-SQLAlchemy — modelo CRUD."""
from uuid import UUID

from trabajos.config.db import db
from ..dominio.repositorios import RepositorioAgendas, RepositorioEventosProcesados
from ..dominio.fabricas import FabricaAgendas
from .dto import AgendaDeTrabajo as AgendaDeTrabajoDbDTO, EventoProcesado
from .mapeadores import MapeadorAgendaDeTrabajoInfra


class RepositorioAgendasSQLAlchemy(RepositorioAgendas):

    def __init__(self):
        self._fabrica: FabricaAgendas = FabricaAgendas()

    def obtener_por_id(self, id: UUID):
        dto = db.session.query(AgendaDeTrabajoDbDTO).filter_by(id=str(id)).one_or_none()
        return None if dto is None else self._fabrica.crear_objeto(dto, MapeadorAgendaDeTrabajoInfra())

    def obtener_todos(self) -> list:
        m = MapeadorAgendaDeTrabajoInfra()
        return [self._fabrica.crear_objeto(d, m) for d in db.session.query(AgendaDeTrabajoDbDTO).all()]

    def contar(self) -> int:
        return db.session.query(AgendaDeTrabajoDbDTO).count()

    def agregar(self, entidad):
        db.session.add(self._fabrica.crear_objeto(entidad, MapeadorAgendaDeTrabajoInfra()))

    def actualizar(self, entidad):
        db.session.merge(self._fabrica.crear_objeto(entidad, MapeadorAgendaDeTrabajoInfra()))

    def eliminar(self, entidad_id):
        db.session.query(AgendaDeTrabajoDbDTO).filter_by(id=str(entidad_id)).delete()


class RepositorioEventosProcesadosSQLAlchemy(RepositorioEventosProcesados):
    def ya_procesado(self, id_evento: str) -> bool:
        return db.session.query(EventoProcesado).filter_by(id_evento=id_evento).one_or_none() is not None

    def agregar(self, id_evento: str):
        db.session.add(EventoProcesado(id_evento=id_evento))
