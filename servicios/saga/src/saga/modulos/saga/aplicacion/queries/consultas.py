"""Queries del orquestador (lado Q): estado de sagas y SAGA LOG."""
from dataclasses import dataclass

from saga.seedwork.aplicacion.queries import Query, QueryHandler, QueryResultado
from saga.seedwork.aplicacion.queries import ejecutar_query as query
from ...infraestructura.fabricas import FabricaRepositorio
from ...dominio.repositorios import RepositorioSagas, RepositorioSagaLog


def _saga_a_dict(s):
    return {"id_saga": str(s.id), "id_cotizacion": s.id_cotizacion, "estado": s.estado.value,
            "paso_actual": s.paso_actual, "pasos_completados": s.pasos_completados,
            "motivo_fallo": s.motivo_fallo, "datos": s.datos,
            "fecha_inicio": s.fecha_inicio.isoformat() if s.fecha_inicio else None,
            "fecha_fin": s.fecha_fin.isoformat() if s.fecha_fin else None,
            "entradas_log": s.secuencia}


def _log_a_dict(e):
    return {"secuencia": e.secuencia, "fecha": e.fecha.isoformat(), "tipo": e.tipo, "paso": e.paso,
            "servicio": e.servicio, "mensaje": e.mensaje, "detalle": e.detalle, "payload": e.payload}


@dataclass
class ObtenerSaga(Query):
    ref: str            # id_saga o id_cotizacion


class ObtenerSagaHandler(QueryHandler):
    def handle(self, q: ObtenerSaga) -> QueryResultado:
        repo = FabricaRepositorio().crear_objeto(RepositorioSagas)
        s = repo.obtener_por_cotizacion(q.ref)
        if s is None:
            try:
                import uuid
                s = repo.obtener_por_id(uuid.UUID(q.ref))
            except ValueError:
                s = None
        if s is None:
            return QueryResultado(resultado=None)
        log = FabricaRepositorio().crear_objeto(RepositorioSagaLog).por_saga(str(s.id))
        d = _saga_a_dict(s)
        d["log"] = [_log_a_dict(e) for e in log]
        return QueryResultado(resultado=d)


@query.register(ObtenerSaga)
def ejecutar_obtener_saga(q: ObtenerSaga):
    return ObtenerSagaHandler().handle(q)


@dataclass
class ListarSagas(Query):
    ...


class ListarSagasHandler(QueryHandler):
    def handle(self, q: ListarSagas) -> QueryResultado:
        repo = FabricaRepositorio().crear_objeto(RepositorioSagas)
        return QueryResultado(resultado={"por_estado": repo.contar_por_estado(),
                                         "sagas": [_saga_a_dict(s) for s in repo.obtener_todos()[:100]]})


@query.register(ListarSagas)
def ejecutar_listar_sagas(q: ListarSagas):
    return ListarSagasHandler().handle(q)


@dataclass
class UltimasEntradasLog(Query):
    n: int = 50


class UltimasEntradasLogHandler(QueryHandler):
    def handle(self, q: UltimasEntradasLog) -> QueryResultado:
        log = FabricaRepositorio().crear_objeto(RepositorioSagaLog)
        filas = list(reversed(log.ultimos(q.n)))
        return QueryResultado(resultado=[dict(_log_a_dict(e), id_saga=e.id_saga) for e in filas])


@query.register(UltimasEntradasLog)
def ejecutar_ultimas(q: UltimasEntradasLog):
    return UltimasEntradasLogHandler().handle(q)
