"""Handlers de aplicación: reaccionan a la señal `PagoRetenidoIntegracion` que la
UoW emite DESPUÉS del commit y despachan el evento al broker."""
from pagos.seedwork.aplicacion.handlers import Handler
from pagos.modulos.pagos.infraestructura.despachadores import Despachador


class HandlerReservaDePagoIntegracion(Handler):

    @staticmethod
    def handle_pago_retenido(evento):
        Despachador().publicar_evento(evento, 'eventos-pago')

    @staticmethod
    def handle_pago_revertido(evento):
        Despachador().publicar_evento(evento, 'eventos-pago')
