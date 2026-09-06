"""Cableado de señales del módulo cotizaciones (igual al tutorial):
las señales `*Integracion` emitidas por la UoW tras el commit se conectan
a los handlers que publican al broker."""
from pydispatch import dispatcher

from .handlers import HandlerCotizacionIntegracion
from ..dominio.eventos import CotizacionCreada, CotizacionAceptada, VisitaSolicitada

dispatcher.connect(HandlerCotizacionIntegracion.handle_cotizacion_creada,
                   signal=f'{CotizacionCreada.__name__}Integracion')
dispatcher.connect(HandlerCotizacionIntegracion.handle_cotizacion_aceptada,
                   signal=f'{CotizacionAceptada.__name__}Integracion')
dispatcher.connect(HandlerCotizacionIntegracion.handle_visita_solicitada,
                   signal=f'{VisitaSolicitada.__name__}Integracion')
