"""Repositorios (ADAPTADORES) del dominio de cotizaciones sobre SQLAlchemy."""
import json
from uuid import UUID

from cotizaciones.config.db import db
from ..dominio.repositorios import RepositorioCotizaciones, RepositorioEventosCotizaciones
from ..dominio.fabricas import FabricaCotizaciones
from .dto import Cotizacion as CotizacionDbDTO, EventosCotizacion
from .mapeadores import MapeadorCotizacionInfra, MapeadorEventosCotizacion


class RepositorioCotizacionesSQLAlchemy(RepositorioCotizaciones):

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
        dtos = db.session.query(CotizacionDbDTO).all()
        m = MapeadorCotizacionInfra()
        return [self.fabrica_cotizaciones.crear_objeto(d, m) for d in dtos]

    def obtener_por_trabajo(self, id_trabajo: str) -> list:
        dtos = db.session.query(CotizacionDbDTO).filter_by(id_trabajo=id_trabajo).all()
        m = MapeadorCotizacionInfra()
        return [self.fabrica_cotizaciones.crear_objeto(d, m) for d in dtos]

    def agregar(self, cotizacion):
        cotizacion_dto = self.fabrica_cotizaciones.crear_objeto(
            cotizacion, MapeadorCotizacionInfra())
        db.session.add(cotizacion_dto)

    def actualizar(self, cotizacion):
        cotizacion_dto = self.fabrica_cotizaciones.crear_objeto(
            cotizacion, MapeadorCotizacionInfra())
        db.session.merge(cotizacion_dto)

    def eliminar(self, cotizacion_id):
        db.session.query(CotizacionDbDTO).filter_by(id=str(cotizacion_id)).delete()


class RepositorioEventosCotizacionSQLAlchemy(RepositorioEventosCotizaciones):
    """EVENT STORE (event sourcing, tutorial 7): persiste cada evento de
    dominio del agregado como registro versionado e inmutable. La UoW lo
    invoca vía `repositorio_eventos_func` al registrar el batch."""

    def __init__(self):
        self._fabrica_cotizaciones: FabricaCotizaciones = FabricaCotizaciones()

    @property
    def fabrica_cotizaciones(self):
        return self._fabrica_cotizaciones

    def obtener_por_id(self, id: UUID) -> list:
        eventos = db.session.query(EventosCotizacion).filter_by(id_entidad=str(id)).all()
        return eventos

    def obtener_todos(self) -> list:
        raise NotImplementedError

    def agregar(self, evento):
        cotizacion_evento = self.fabrica_cotizaciones.crear_objeto(
            evento, MapeadorEventosCotizacion())

        evento_dto = EventosCotizacion()
        evento_dto.id = str(evento.id)
        evento_dto.id_entidad = str(evento.id_cotizacion)
        evento_dto.fecha_evento = evento.fecha_evento
        evento_dto.version = str(cotizacion_evento.specversion)
        evento_dto.tipo_evento = evento.__class__.__name__
        evento_dto.formato_contenido = 'JSON'
        evento_dto.nombre_servicio = str(cotizacion_evento.service_name)
        evento_dto.contenido = json.dumps(cotizacion_evento.data.__dict__)

        db.session.add(evento_dto)

    def actualizar(self, evento):
        raise NotImplementedError('Un event store es inmutable: no se actualiza')

    def eliminar(self, evento_id):
        raise NotImplementedError('Un event store es inmutable: no se elimina')
