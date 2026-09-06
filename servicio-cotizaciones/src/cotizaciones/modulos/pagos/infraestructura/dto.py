from datetime import datetime

from cotizaciones.config.db import db


class ReservaPago(db.Model):
    __tablename__ = "reservas_pago"
    id = db.Column(db.String, primary_key=True)
    id_cotizacion = db.Column(db.String, nullable=False, index=True)
    id_trabajo = db.Column(db.String, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    moneda = db.Column(db.String, nullable=False)
    estado = db.Column(db.String, nullable=False, default="RETENIDO")
    fecha = db.Column(db.DateTime, default=datetime.now)
