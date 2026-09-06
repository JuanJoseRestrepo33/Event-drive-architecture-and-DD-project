"""Query ObtenerCotizacion (lado Q de CQS): solo lectura, retorna DTO."""
from dataclasses import dataclass
import uuid

from cotizaciones.seedwork.aplicacion.queries import Query, QueryHandler, QueryResultado
from cotizaciones.seedwork.aplicacion.queries import ejecutar_query as query
from ..mapeadores import MapeadorCotizacion
from ...infraestructura.fabricas import FabricaRepositorio
from ...dominio.repositorios import RepositorioCotizaciones


@dataclass
class ObtenerCotizacion(Query):
    id: str


class ObtenerCotizacionHandler(QueryHandler):
    def handle(self, query: ObtenerCotizacion) -> QueryResultado:
        repositorio = FabricaRepositorio().crear_objeto(RepositorioCotizaciones)
        cotizacion = repositorio.obtener_por_id(uuid.UUID(query.id))
        if cotizacion is None:
            return QueryResultado(resultado=None)
        return QueryResultado(resultado=MapeadorCotizacion().entidad_a_dto(cotizacion))


@query.register(ObtenerCotizacion)
def ejecutar_query_obtener_cotizacion(query: ObtenerCotizacion):
    handler = ObtenerCotizacionHandler()
    return handler.handle(query)
