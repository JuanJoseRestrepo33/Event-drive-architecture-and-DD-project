"""Cableado de señales (pydispatch) del módulo, como en el tutorial."""
from pydispatch import dispatcher

from .handlers import HandlerCotizacionIntegracion
from cotizaciones.modulos.cotizaciones.dominio.eventos import CotizacionCreada, CotizacionAceptada

dispatcher.connect(HandlerCotizacionIntegracion.handle_cotizacion_creada,
                   signal=f'{CotizacionCreada.__name__}Integracion')
dispatcher.connect(HandlerCotizacionIntegracion.handle_cotizacion_aceptada,
                   signal=f'{CotizacionAceptada.__name__}Integracion')
