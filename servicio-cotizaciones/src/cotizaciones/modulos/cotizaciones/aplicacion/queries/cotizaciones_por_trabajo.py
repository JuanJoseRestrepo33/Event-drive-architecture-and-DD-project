"""Query CotizacionesPorTrabajo (lado Q de CQS)."""
from dataclasses import dataclass

from cotizaciones.seedwork.aplicacion.queries import Query, QueryHandler, QueryResultado
from cotizaciones.seedwork.aplicacion.queries import ejecutar_query as query
from ..mapeadores import MapeadorCotizacion
from ...infraestructura.fabricas import FabricaRepositorio
from ...dominio.repositorios import RepositorioCotizaciones


@dataclass
class CotizacionesPorTrabajo(Query):
    id_trabajo: str


class CotizacionesPorTrabajoHandler(QueryHandler):
    def handle(self, query: CotizacionesPorTrabajo) -> QueryResultado:
        repositorio = FabricaRepositorio().crear_objeto(RepositorioCotizaciones)
        m = MapeadorCotizacion()
        cotizaciones = repositorio.obtener_por_trabajo(query.id_trabajo)
        return QueryResultado(resultado=[m.entidad_a_dto(c) for c in cotizaciones])


@query.register(CotizacionesPorTrabajo)
def ejecutar_query_cotizaciones_por_trabajo(query: CotizacionesPorTrabajo):
    handler = CotizacionesPorTrabajoHandler()
    return handler.handle(query)
