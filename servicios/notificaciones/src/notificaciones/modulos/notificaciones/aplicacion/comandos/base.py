from notificaciones.seedwork.aplicacion.comandos import ComandoHandler
from notificaciones.modulos.notificaciones.infraestructura.fabricas import FabricaRepositorio
from notificaciones.modulos.notificaciones.dominio.fabricas import FabricaNotificaciones


class ComandoNotificacionBaseHandler(ComandoHandler):
    def __init__(self):
        self._fabrica_repositorio: FabricaRepositorio = FabricaRepositorio()
        self._fabrica: FabricaNotificaciones = FabricaNotificaciones()

    @property
    def fabrica_repositorio(self):
        return self._fabrica_repositorio

    @property
    def fabrica(self):
        return self._fabrica
