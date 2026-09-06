"""DTOs (modelos) de la capa de infraestructura del dominio de cotizaciones.
Como en el tutorial, los modelos de la BD viven en `infraestructura/dto.py`."""
from cotizaciones.config.db import db

Base = db.declarative_base()


class Cotizacion(db.Model):
    __tablename__ = "cotizaciones"
    id = db.Column(db.String, primary_key=True)
    id_trabajo = db.Column(db.String, nullable=False, index=True)
    id_proveedor = db.Column(db.String, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    moneda = db.Column(db.String, nullable=False)
    categoria = db.Column(db.String, nullable=False)
    descripcion = db.Column(db.String, nullable=False)
    vigencia_desde = db.Column(db.DateTime, nullable=False)
    vigencia_hasta = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String, nullable=False)
    fecha_creacion = db.Column(db.DateTime, nullable=False)
    visitas = db.relationship('VisitaCotizacion', cascade='all, delete-orphan',
                              backref='cotizacion', lazy='joined')


class VisitaCotizacion(db.Model):
    __tablename__ = "visitas_cotizacion"
    id = db.Column(db.String, primary_key=True)
    id_cotizacion = db.Column(db.String, db.ForeignKey('cotizaciones.id'), nullable=False)
    fecha_propuesta = db.Column(db.DateTime, nullable=False)
    confirmada = db.Column(db.Boolean, default=False)


class EventosCotizacion(db.Model):
    """EVENT STORE (event sourcing, tutorial 7): registro histórico e
    inmutable de cada evento de dominio del agregado Cotizacion."""
    __tablename__ = "eventos_cotizacion"
    id = db.Column(db.String, primary_key=True)
    id_entidad = db.Column(db.String, nullable=False, index=True)
    fecha_evento = db.Column(db.DateTime, nullable=False)
    version = db.Column(db.String, nullable=False)
    tipo_evento = db.Column(db.String, nullable=False)
    formato_contenido = db.Column(db.String, nullable=False)
    nombre_servicio = db.Column(db.String, nullable=False)
    contenido = db.Column(db.Text, nullable=False)
