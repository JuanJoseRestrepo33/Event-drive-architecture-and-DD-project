"""Handlers de aplicación: reaccionan a la señal `TrabajoAgendadoIntegracion` que la
UoW emite DESPUÉS del commit y despachan el evento al broker."""
from trabajos.seedwork.aplicacion.handlers import Handler
from trabajos.modulos.trabajos.infraestructura.despachadores import Despachador


class HandlerAgendaDeTrabajoIntegracion(Handler):

    @staticmethod
    def handle_trabajo_agendado(evento):
        Despachador().publicar_evento(evento, 'eventos-trabajo')

    @staticmethod
    def handle_trabajo_rechazado(evento):
        Despachador().publicar_evento(evento, 'eventos-trabajo')
