from cotizaciones.seedwork.aplicacion.comandos import ComandoHandler
from cotizaciones.modulos.cotizaciones.infraestructura.fabricas import FabricaRepositorio
from cotizaciones.modulos.cotizaciones.dominio.fabricas import FabricaCotizaciones


class ComandoCotizacionBaseHandler(ComandoHandler):
    def __init__(self):
        self._fabrica_repositorio: FabricaRepositorio = FabricaRepositorio()
        self._fabrica_cotizaciones: FabricaCotizaciones = FabricaCotizaciones()

    @property
    def fabrica_repositorio(self):
        return self._fabrica_repositorio

    @property
    def fabrica_cotizaciones(self):
        return self._fabrica_cotizaciones
