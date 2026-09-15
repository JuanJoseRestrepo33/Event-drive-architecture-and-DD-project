"""Query ListarAgendas (lado Q de CQS): solo lectura, retorna DTOs."""
from dataclasses import dataclass

from trabajos.seedwork.aplicacion.queries import Query, QueryHandler, QueryResultado
from trabajos.seedwork.aplicacion.queries import ejecutar_query as query
from ..mapeadores import MapeadorAgendaDeTrabajo
from ...infraestructura.fabricas import FabricaRepositorio
from ...dominio.repositorios import RepositorioAgendas


@dataclass
class ListarAgendas(Query):
    ...


class ListarAgendasHandler(QueryHandler):
    def handle(self, query: ListarAgendas) -> QueryResultado:
        repositorio = FabricaRepositorio().crear_objeto(RepositorioAgendas)
        m = MapeadorAgendaDeTrabajo()
        return QueryResultado(resultado=[m.entidad_a_dto(e) for e in repositorio.obtener_todos()])


@query.register(ListarAgendas)
def ejecutar_query_listar(query: ListarAgendas):
    return ListarAgendasHandler().handle(query)
