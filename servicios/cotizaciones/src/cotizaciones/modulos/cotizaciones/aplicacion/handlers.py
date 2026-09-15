"""Handlers de aplicación: reaccionan a las señales `*Integracion` que la
Unidad de Trabajo emite DESPUÉS del commit y despachan el evento de
integración al broker (tópico eventos-cotizacion)."""
from cotizaciones.seedwork.aplicacion.handlers import Handler
from cotizaciones.modulos.cotizaciones.infraestructura.despachadores import Despachador


class HandlerCotizacionIntegracion(Handler):

    @staticmethod
    def handle_cotizacion_creada(evento):
        Despachador().publicar_evento(evento, 'eventos-cotizacion')

    @staticmethod
    def handle_cotizacion_aceptada(evento):
        Despachador().publicar_evento(evento, 'eventos-cotizacion')
