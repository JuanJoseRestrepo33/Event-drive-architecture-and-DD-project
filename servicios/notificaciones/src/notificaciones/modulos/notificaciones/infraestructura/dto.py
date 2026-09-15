"""Modelos de la BD (Flask-SQLAlchemy). Topología DESCENTRALIZADA: BD
exclusiva del servicio de notificaciones. Modelo CRUD + tabla de idempotencia."""
from notificaciones.config.db import db


class Notificacion(db.Model):
    __tablename__ = "notificaciones"
    id = db.Column(db.String, primary_key=True)
    tipo = db.Column(db.String, nullable=False)
    version = db.Column(db.String, nullable=False)
    destinatario = db.Column(db.String, nullable=False)
    mensaje = db.Column(db.String, nullable=False)
    estado = db.Column(db.String, nullable=False)


class EventoProcesado(db.Model):
    """IDEMPOTENCIA del consumidor: ids de mensajes ya aplicados."""
    __tablename__ = "eventos_procesados"
    id_evento = db.Column(db.String, primary_key=True)
