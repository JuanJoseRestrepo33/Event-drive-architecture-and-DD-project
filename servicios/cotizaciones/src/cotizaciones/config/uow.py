"""Unidad de Trabajo sobre SQLAlchemy (adaptador concreto del puerto UoW)."""
from cotizaciones.config.db import db
from cotizaciones.seedwork.infraestructura.uow import UnidadTrabajo, Batch


class ExcepcionUoW(Exception):
    ...


class UnidadTrabajoSQLAlchemy(UnidadTrabajo):

    def __init__(self):
        self._batches: list[Batch] = list()

    def __getstate__(self):
        # La sesión de SQLAlchemy no se serializa: solo los batches
        return {'_batches': self._batches}

    def __setstate__(self, state):
        self._batches = state['_batches']

    def _limpiar_batches(self):
        self._batches = list()

    @property
    def batches(self) -> list[Batch]:
        return self._batches

    def commit(self):
        for batch in self.batches:
            batch.operacion(*batch.args, **batch.kwargs)
        db.session.commit()
        super().commit()

    def rollback(self, savepoint=None):
        if savepoint:
            savepoint.rollback()
        else:
            db.session.rollback()
        super().rollback()

    def savepoint(self):
        ...
