"""COMUNICACIÓN ENTRE MÓDULOS POR EVENTOS DE DOMINIO (rúbrica, 9pt).

El módulo pagos NO es invocado por cotizaciones: se conecta a la señal
`CotizacionAceptadaDominio` que la Unidad de Trabajo emite al registrar el
batch (pydispatch, igual al tutorial). Al ocurrir el hecho, retiene el
pago (escrow) creando una ReservaPago dentro de la MISMA transacción de la
UoW (el commit es único). Cotizaciones no conoce a pagos."""
import uuid

from cotizaciones.seedwork.aplicacion.handlers import Handler
from cotizaciones.config.db import db
from ..infraestructura.dto import ReservaPago


class HandlerCotizacionDominio(Handler):

    @staticmethod
    def handle_cotizacion_aceptada(evento):
        reserva = ReservaPago(
            id=str(uuid.uuid4()),
            id_cotizacion=str(evento.id_cotizacion),
            id_trabajo=evento.id_trabajo,
            monto=evento.monto, moneda=evento.moneda,
            estado="RETENIDO")
        db.session.add(reserva)
