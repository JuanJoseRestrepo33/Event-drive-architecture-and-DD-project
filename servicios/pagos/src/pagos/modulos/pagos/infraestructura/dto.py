"""Modelos de la BD (Flask-SQLAlchemy). Topología DESCENTRALIZADA: BD
exclusiva del servicio de pagos. Modelo CRUD + tabla de idempotencia."""
from pagos.config.db import db


class ReservaDePago(db.Model):
    __tablename__ = "reservas_pago"
    id = db.Column(db.String, primary_key=True)
    id_cotizacion = db.Column(db.String, nullable=False, unique=True)
    id_trabajo = db.Column(db.String, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    moneda = db.Column(db.String, nullable=False)
    pais = db.Column(db.String, nullable=False)
    estado = db.Column(db.String, nullable=False)


class EventoProcesado(db.Model):
    """IDEMPOTENCIA del consumidor: ids de mensajes ya aplicados."""
    __tablename__ = "eventos_procesados"
    id_evento = db.Column(db.String, primary_key=True)
