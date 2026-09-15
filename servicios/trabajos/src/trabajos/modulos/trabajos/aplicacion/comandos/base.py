from trabajos.seedwork.aplicacion.comandos import ComandoHandler
from trabajos.modulos.trabajos.infraestructura.fabricas import FabricaRepositorio
from trabajos.modulos.trabajos.dominio.fabricas import FabricaAgendas


class ComandoAgendaDeTrabajoBaseHandler(ComandoHandler):
    def __init__(self):
        self._fabrica_repositorio: FabricaRepositorio = FabricaRepositorio()
        self._fabrica: FabricaAgendas = FabricaAgendas()

    @property
    def fabrica_repositorio(self):
        return self._fabrica_repositorio

    @property
    def fabrica(self):
        return self._fabrica
