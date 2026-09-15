"""Query HistoriaCotizacion: lee el EVENT STORE y muestra el agregado
reconstruido por replay (demuestra event sourcing en la consulta)."""
from dataclasses import dataclass
import uuid

from cotizaciones.seedwork.aplicacion.queries import Query, QueryHandler, QueryResultado
from cotizaciones.seedwork.aplicacion.queries import ejecutar_query as query
from ..mapeadores import MapeadorCotizacion
from ...infraestructura.fabricas import FabricaRepositorio
from ...dominio.repositorios import RepositorioEventosCotizaciones


@dataclass
class HistoriaCotizacion(Query):
    id: str


class HistoriaCotizacionHandler(QueryHandler):
    def handle(self, query: HistoriaCotizacion) -> QueryResultado:
        repositorio_eventos = FabricaRepositorio().crear_objeto(RepositorioEventosCotizaciones)
        eventos = repositorio_eventos.obtener_por_id(uuid.UUID(query.id))
        if not eventos:
            return QueryResultado(resultado=None)
        reconstruida = repositorio_eventos.reconstruir(uuid.UUID(query.id))
        return QueryResultado(resultado={
            "reconstruida_por_replay": MapeadorCotizacion().entidad_a_dto(reconstruida).__dict__,
            "historia": [{"seq": e.seq, "tipo": e.tipo_evento, "version": e.version,
                          "fecha": e.fecha_evento.isoformat(), "contenido": e.contenido}
                         for e in eventos]})


@query.register(HistoriaCotizacion)
def ejecutar_query_historia_cotizacion(query: HistoriaCotizacion):
    return HistoriaCotizacionHandler().handle(query)
