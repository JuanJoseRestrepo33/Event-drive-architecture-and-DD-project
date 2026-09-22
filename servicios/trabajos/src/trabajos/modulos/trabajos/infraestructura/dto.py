"""Modelos de la BD (Flask-SQLAlchemy). Topología DESCENTRALIZADA: BD
exclusiva del servicio de trabajos. Modelo CRUD + tabla de idempotencia."""
from trabajos.config.db import db


class AgendaDeTrabajo(db.Model):
    __tablename__ = "agendas_trabajo"
    id = db.Column(db.String, primary_key=True)
    id_trabajo = db.Column(db.String, nullable=False)
    id_cotizacion = db.Column(db.String, nullable=False, unique=True)
    id_pago = db.Column(db.String, nullable=False)
    pais = db.Column(db.String, nullable=False)
    id_proveedor = db.Column(db.String, nullable=True)
    estado = db.Column(db.String, nullable=False)


class EventoProcesado(db.Model):
    """IDEMPOTENCIA del consumidor: ids de mensajes ya aplicados."""
    __tablename__ = "eventos_procesados"
    id_evento = db.Column(db.String, primary_key=True)
