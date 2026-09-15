"""Cableado de señales (pydispatch) del módulo, como en el tutorial."""
from pydispatch import dispatcher

from .handlers import HandlerReservaDePagoIntegracion
from pagos.modulos.pagos.dominio.eventos import PagoRetenido

dispatcher.connect(HandlerReservaDePagoIntegracion.handle_pago_retenido,
                   signal=f'{PagoRetenido.__name__}Integracion')
