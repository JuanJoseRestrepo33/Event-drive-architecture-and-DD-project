"""Query ListarReservas (lado Q de CQS): solo lectura, retorna DTOs."""
from dataclasses import dataclass

from pagos.seedwork.aplicacion.queries import Query, QueryHandler, QueryResultado
from pagos.seedwork.aplicacion.queries import ejecutar_query as query
from ..mapeadores import MapeadorReservaDePago
from ...infraestructura.fabricas import FabricaRepositorio
from ...dominio.repositorios import RepositorioReservas


@dataclass
class ListarReservas(Query):
    ...


class ListarReservasHandler(QueryHandler):
    def handle(self, query: ListarReservas) -> QueryResultado:
        repositorio = FabricaRepositorio().crear_objeto(RepositorioReservas)
        m = MapeadorReservaDePago()
        return QueryResultado(resultado=[m.entidad_a_dto(e) for e in repositorio.obtener_todos()])


@query.register(ListarReservas)
def ejecutar_query_listar(query: ListarReservas):
    return ListarReservasHandler().handle(query)
