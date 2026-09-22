"""Repositorios (adaptadores) del orquestador sobre Flask-SQLAlchemy."""
import json
import uuid
from uuid import UUID

from saga.config.db import db
from ..dominio.entidades import Saga, EntradaSagaLog
from ..dominio.objetos_valor import EstadoSaga
from ..dominio.repositorios import RepositorioSagas, RepositorioSagaLog, RepositorioEventosProcesados
from .dto import Saga as SagaDbDTO, SagaLog, EventoProcesado


def _a_entidad(dto: SagaDbDTO) -> Saga:
    s = Saga()
    s._id = uuid.UUID(dto.id)
    s.id_cotizacion = dto.id_cotizacion
    s.estado = EstadoSaga(dto.estado)
    s.paso_actual = dto.paso_actual
    s.pasos_completados = json.loads(dto.pasos_completados or "[]")
    s.datos = json.loads(dto.datos or "{}")
    s.secuencia = dto.secuencia
    s.motivo_fallo = dto.motivo_fallo
    s.fecha_inicio = dto.fecha_inicio
    s.fecha_fin = dto.fecha_fin
    return s


def _a_dto(s: Saga) -> SagaDbDTO:
    dto = SagaDbDTO()
    dto.id = str(s.id)
    dto.id_cotizacion = s.id_cotizacion
    dto.estado = s.estado.value
    dto.paso_actual = s.paso_actual
    dto.pasos_completados = json.dumps(s.pasos_completados)
    dto.datos = json.dumps(s.datos, ensure_ascii=False)
    dto.secuencia = s.secuencia
    dto.motivo_fallo = s.motivo_fallo
    dto.fecha_inicio = s.fecha_inicio
    dto.fecha_fin = s.fecha_fin
    return dto


class RepositorioSagasSQLAlchemy(RepositorioSagas):
    def obtener_por_id(self, id: UUID):
        dto = db.session.query(SagaDbDTO).filter_by(id=str(id)).one_or_none()
        return None if dto is None else _a_entidad(dto)

    def obtener_por_cotizacion(self, id_cotizacion: str):
        dto = db.session.query(SagaDbDTO).filter_by(id_cotizacion=id_cotizacion).one_or_none()
        return None if dto is None else _a_entidad(dto)

    def obtener_todos(self) -> list:
        return [_a_entidad(d) for d in db.session.query(SagaDbDTO).order_by(SagaDbDTO.fecha_inicio.desc()).all()]

    def contar_por_estado(self) -> dict:
        filas = db.session.query(SagaDbDTO.estado, db.func.count()).group_by(SagaDbDTO.estado).all()
        return {e: n for e, n in filas}

    def agregar(self, saga: Saga):
        db.session.add(_a_dto(saga))

    def actualizar(self, saga: Saga):
        db.session.merge(_a_dto(saga))

    def eliminar(self, id):
        raise NotImplementedError


class RepositorioSagaLogSQLAlchemy(RepositorioSagaLog):
    def agregar(self, entrada: EntradaSagaLog):
        fila = SagaLog(id_saga=entrada.id_saga, secuencia=entrada.secuencia, fecha=entrada.fecha_evento,
                       tipo=entrada.tipo, paso=entrada.paso, servicio=entrada.servicio,
                       mensaje=entrada.mensaje, detalle=entrada.detalle, payload=entrada.payload)
        db.session.add(fila)

    def por_saga(self, id_saga: str) -> list:
        return db.session.query(SagaLog).filter_by(id_saga=id_saga).order_by(SagaLog.secuencia).all()

    def ultimos(self, n: int = 50) -> list:
        return db.session.query(SagaLog).order_by(SagaLog.id.desc()).limit(n).all()


class RepositorioEventosProcesadosSQLAlchemy(RepositorioEventosProcesados):
    def ya_procesado(self, id_evento: str) -> bool:
        return db.session.query(EventoProcesado).filter_by(id_evento=id_evento).one_or_none() is not None

    def agregar(self, id_evento: str):
        db.session.add(EventoProcesado(id_evento=id_evento))
