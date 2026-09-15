"""Repositorios (ADAPTADORES) sobre Flask-SQLAlchemy."""
import json
from uuid import UUID

from cotizaciones.config.db import db
from ..dominio.repositorios import RepositorioCotizaciones, RepositorioEventosCotizaciones
from ..dominio.fabricas import FabricaCotizaciones
from ..dominio.entidades import Cotizacion
from ..dominio.eventos import CotizacionCreada, CotizacionAceptada
from .dto import Cotizacion as CotizacionDbDTO, EventosCotizacion
from .mapeadores import MapeadorCotizacionInfra, MapeadorEventosCotizacion


class RepositorioCotizacionesSQLAlchemy(RepositorioCotizaciones):
    """PROYECCIÓN: read model que se mantiene en la misma UoW que el store."""

    def __init__(self):
        self._fabrica_cotizaciones: FabricaCotizaciones = FabricaCotizaciones()

    @property
    def fabrica_cotizaciones(self):
        return self._fabrica_cotizaciones

    def obtener_por_id(self, id: UUID):
        dto = db.session.query(CotizacionDbDTO).filter_by(id=str(id)).one_or_none()
        if dto is None:
            return None
        return self.fabrica_cotizaciones.crear_objeto(dto, MapeadorCotizacionInfra())

    def obtener_todos(self) -> list:
        m = MapeadorCotizacionInfra()
        return [self.fabrica_cotizaciones.crear_objeto(d, m)
                for d in db.session.query(CotizacionDbDTO).all()]

    def obtener_por_trabajo(self, id_trabajo: str) -> list:
        m = MapeadorCotizacionInfra()
        return [self.fabrica_cotizaciones.crear_objeto(d, m)
                for d in db.session.query(CotizacionDbDTO).filter_by(id_trabajo=id_trabajo).all()]

    def agregar(self, cotizacion):
        db.session.add(self.fabrica_cotizaciones.crear_objeto(cotizacion, MapeadorCotizacionInfra()))

    def actualizar(self, cotizacion):
        db.session.merge(self.fabrica_cotizaciones.crear_objeto(cotizacion, MapeadorCotizacionInfra()))

    def eliminar(self, cotizacion_id):
        db.session.query(CotizacionDbDTO).filter_by(id=str(cotizacion_id)).delete()


class RepositorioEventosCotizacionSQLAlchemy(RepositorioEventosCotizaciones):
    """EVENT STORE: cada evento de dominio se persiste como registro
    versionado e inmutable (la UoW lo invoca vía `repositorio_eventos_func`).
    `reconstruir` reproduce la historia para obtener el agregado."""
    TIPOS = {"CotizacionCreada": CotizacionCreada, "CotizacionAceptada": CotizacionAceptada}

    def __init__(self):
        self._mapeador = MapeadorEventosCotizacion()

    def obtener_por_id(self, id: UUID) -> list:
        return (db.session.query(EventosCotizacion).filter_by(id_entidad=str(id))
                .order_by(EventosCotizacion.seq).all())

    def reconstruir(self, id: UUID):
        filas = self.obtener_por_id(id)
        if not filas:
            return None
        eventos = []
        for fila in filas:
            datos = json.loads(fila.contenido)
            evento = self.TIPOS[fila.tipo_evento](**datos)
            evento._id = UUID(fila.id)
            eventos.append(evento)
        return Cotizacion.desde_historia(eventos)

    def obtener_todos(self) -> list:
        return db.session.query(EventosCotizacion).order_by(EventosCotizacion.seq).all()

    def contar(self) -> int:
        return db.session.query(EventosCotizacion).count()

    def agregar(self, evento):
        integracion = self._mapeador.entidad_a_dto(evento)
        fila = EventosCotizacion()
        fila.id = str(evento.id)
        fila.id_entidad = str(evento.id_cotizacion)
        fila.fecha_evento = evento.fecha_evento
        fila.version = str(integracion.specversion)
        fila.tipo_evento = evento.__class__.__name__
        fila.formato_contenido = 'JSON'
        fila.nombre_servicio = str(integracion.service_name)
        fila.contenido = json.dumps({
            "id_cotizacion": str(evento.id_cotizacion), "id_trabajo": evento.id_trabajo,
            "id_proveedor": evento.id_proveedor, "monto": evento.monto,
            "moneda": evento.moneda, "pais": evento.pais})
        db.session.add(fila)

    def actualizar(self, evento):
        raise NotImplementedError('Un event store es inmutable: no se actualiza')

    def eliminar(self, evento_id):
        raise NotImplementedError('Un event store es inmutable: no se elimina')
