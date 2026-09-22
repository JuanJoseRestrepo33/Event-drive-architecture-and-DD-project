"""Repositorios (ADAPTADORES) sobre Flask-SQLAlchemy — modelo CRUD."""
from uuid import UUID

from pagos.config.db import db
from ..dominio.repositorios import RepositorioReservas, RepositorioEventosProcesados
from ..dominio.fabricas import FabricaReservas
from .dto import ReservaDePago as ReservaDePagoDbDTO, EventoProcesado
from .mapeadores import MapeadorReservaDePagoInfra


class RepositorioReservasSQLAlchemy(RepositorioReservas):

    def __init__(self):
        self._fabrica: FabricaReservas = FabricaReservas()

    def obtener_por_id(self, id: UUID):
        dto = db.session.query(ReservaDePagoDbDTO).filter_by(id=str(id)).one_or_none()
        return None if dto is None else self._fabrica.crear_objeto(dto, MapeadorReservaDePagoInfra())

    def obtener_todos(self) -> list:
        m = MapeadorReservaDePagoInfra()
        return [self._fabrica.crear_objeto(d, m) for d in db.session.query(ReservaDePagoDbDTO).all()]

    def contar(self) -> int:
        return db.session.query(ReservaDePagoDbDTO).count()

    def obtener_por_cotizacion(self, id_cotizacion: str):
        dto = db.session.query(ReservaDePagoDbDTO).filter_by(id_cotizacion=id_cotizacion).one_or_none()
        return None if dto is None else self._fabrica.crear_objeto(dto, MapeadorReservaDePagoInfra())

    def agregar(self, entidad):
        db.session.add(self._fabrica.crear_objeto(entidad, MapeadorReservaDePagoInfra()))

    def actualizar(self, entidad):
        db.session.merge(self._fabrica.crear_objeto(entidad, MapeadorReservaDePagoInfra()))

    def eliminar(self, entidad_id):
        db.session.query(ReservaDePagoDbDTO).filter_by(id=str(entidad_id)).delete()


class RepositorioEventosProcesadosSQLAlchemy(RepositorioEventosProcesados):
    def ya_procesado(self, id_evento: str) -> bool:
        return db.session.query(EventoProcesado).filter_by(id_evento=id_evento).one_or_none() is not None

    def agregar(self, id_evento: str):
        db.session.add(EventoProcesado(id_evento=id_evento))
