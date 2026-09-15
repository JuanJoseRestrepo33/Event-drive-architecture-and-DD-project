from pagos.seedwork.aplicacion.comandos import ComandoHandler
from pagos.modulos.pagos.infraestructura.fabricas import FabricaRepositorio
from pagos.modulos.pagos.dominio.fabricas import FabricaReservas


class ComandoReservaDePagoBaseHandler(ComandoHandler):
    def __init__(self):
        self._fabrica_repositorio: FabricaRepositorio = FabricaRepositorio()
        self._fabrica: FabricaReservas = FabricaReservas()

    @property
    def fabrica_repositorio(self):
        return self._fabrica_repositorio

    @property
    def fabrica(self):
        return self._fabrica
