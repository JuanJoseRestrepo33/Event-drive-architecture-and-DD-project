"""Suscripción del módulo pagos a los eventos de DOMINIO de cotizaciones."""
from pydispatch import dispatcher

from .handlers import HandlerCotizacionDominio
from cotizaciones.modulos.cotizaciones.dominio.eventos import CotizacionAceptada

dispatcher.connect(HandlerCotizacionDominio.handle_cotizacion_aceptada,
                   signal=f'{CotizacionAceptada.__name__}Dominio')
