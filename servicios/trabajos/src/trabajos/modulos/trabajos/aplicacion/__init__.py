"""Cableado de señales (pydispatch) del módulo, como en el tutorial."""
from pydispatch import dispatcher

from .handlers import HandlerAgendaDeTrabajoIntegracion
from trabajos.modulos.trabajos.dominio.eventos import TrabajoAgendado, TrabajoRechazado

dispatcher.connect(HandlerAgendaDeTrabajoIntegracion.handle_trabajo_agendado,
                   signal=f'{TrabajoAgendado.__name__}Integracion')
dispatcher.connect(HandlerAgendaDeTrabajoIntegracion.handle_trabajo_rechazado,
                   signal=f'{TrabajoRechazado.__name__}Integracion')
