"""Handlers de aplicación: reaccionan a las señales `*Integracion` que la
Unidad de Trabajo emite DESPUÉS del commit y despachan el evento hacia el
broker (tópico eventos-cotizacion) — igual que en el tutorial."""
from cotizaciones.seedwork.aplicacion.handlers import Handler
from cotizaciones.modulos.cotizaciones.infraestructura.despachadores import Despachador


class HandlerCotizacionIntegracion(Handler):

    @staticmethod
    def handle_cotizacion_creada(evento):
        despachador = Despachador()
        despachador.publicar_evento(evento, 'eventos-cotizacion')

    @staticmethod
    def handle_cotizacion_aceptada(evento):
        despachador = Despachador()
        despachador.publicar_evento(evento, 'eventos-cotizacion')

    @staticmethod
    def handle_visita_solicitada(evento):
        despachador = Despachador()
        despachador.publicar_evento(evento, 'eventos-cotizacion')
