"""Query ListarNotificaciones (lado Q de CQS): solo lectura, retorna DTOs."""
from dataclasses import dataclass

from notificaciones.seedwork.aplicacion.queries import Query, QueryHandler, QueryResultado
from notificaciones.seedwork.aplicacion.queries import ejecutar_query as query
from ..mapeadores import MapeadorNotificacion
from ...infraestructura.fabricas import FabricaRepositorio
from ...dominio.repositorios import RepositorioNotificaciones


@dataclass
class ListarNotificaciones(Query):
    ...


class ListarNotificacionesHandler(QueryHandler):
    def handle(self, query: ListarNotificaciones) -> QueryResultado:
        repositorio = FabricaRepositorio().crear_objeto(RepositorioNotificaciones)
        m = MapeadorNotificacion()
        return QueryResultado(resultado=[m.entidad_a_dto(e) for e in repositorio.obtener_todos()])


@query.register(ListarNotificaciones)
def ejecutar_query_listar(query: ListarNotificaciones):
    return ListarNotificacionesHandler().handle(query)
