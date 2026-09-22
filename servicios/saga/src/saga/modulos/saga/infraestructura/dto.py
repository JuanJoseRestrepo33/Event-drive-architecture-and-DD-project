"""Modelos de la BD del orquestador (Flask-SQLAlchemy). BD propia (topología
descentralizada). Aquí vive el SAGA LOG."""
from saga.config.db import db


class Saga(db.Model):
    """Estado actual de cada transacción larga (para monitoreo y reanudación)."""
    __tablename__ = "sagas"
    id = db.Column(db.String, primary_key=True)
    id_cotizacion = db.Column(db.String, nullable=False, unique=True, index=True)
    estado = db.Column(db.String, nullable=False, index=True)
    paso_actual = db.Column(db.String, nullable=True)
    pasos_completados = db.Column(db.String, nullable=False, default="[]")   # JSON
    datos = db.Column(db.Text, nullable=False, default="{}")                  # JSON
    secuencia = db.Column(db.Integer, nullable=False, default=0)
    motivo_fallo = db.Column(db.String, nullable=True)
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime, nullable=True)


class SagaLog(db.Model):
    """SAGA LOG: una fila por transición (append-only). Consultable con SQL."""
    __tablename__ = "saga_log"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_saga = db.Column(db.String, nullable=False, index=True)
    secuencia = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    tipo = db.Column(db.String, nullable=False, index=True)     # INICIO, COMANDO_ENVIADO, EVENTO_RECIBIDO, PASO_OK, PASO_FALLIDO, COMPENSACION_ENVIADA, COMPENSACION_OK, FIN
    paso = db.Column(db.String, nullable=True)
    servicio = db.Column(db.String, nullable=True)
    mensaje = db.Column(db.String, nullable=True)               # comando/evento
    detalle = db.Column(db.String, nullable=True)
    payload = db.Column(db.Text, nullable=True)                 # JSON


class EventoProcesado(db.Model):
    __tablename__ = "eventos_procesados"
    id_evento = db.Column(db.String, primary_key=True)
