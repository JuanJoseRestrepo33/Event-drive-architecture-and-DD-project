"""Modelos de la BD (Flask-SQLAlchemy), como en el tutorial: la
infraestructura del módulo define sus tablas. Topología DESCENTRALIZADA:
esta BD es exclusiva del servicio de cotizaciones."""
from cotizaciones.config.db import db


class Cotizacion(db.Model):
    """PROYECCIÓN (read model) del agregado: la consultan las queries."""
    __tablename__ = "cotizaciones"
    id = db.Column(db.String, primary_key=True)
    id_trabajo = db.Column(db.String, nullable=False, index=True)
    id_proveedor = db.Column(db.String, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    moneda = db.Column(db.String, nullable=False)
    pais = db.Column(db.String, nullable=False, default="CO")
    estado = db.Column(db.String, nullable=False)
    version = db.Column(db.Integer, nullable=False, default=0)


class EventosCotizacion(db.Model):
    """EVENT STORE (event sourcing): append-only, fuente de verdad."""
    __tablename__ = "eventos_cotizacion"
    seq = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id = db.Column(db.String, nullable=False, unique=True)
    id_entidad = db.Column(db.String, nullable=False, index=True)
    fecha_evento = db.Column(db.DateTime, nullable=False)
    version = db.Column(db.String, nullable=False)          # specversion del contrato
    tipo_evento = db.Column(db.String, nullable=False)
    formato_contenido = db.Column(db.String, nullable=False)
    nombre_servicio = db.Column(db.String, nullable=False)
    contenido = db.Column(db.Text, nullable=False)
