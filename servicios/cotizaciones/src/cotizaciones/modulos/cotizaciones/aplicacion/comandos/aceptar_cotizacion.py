"""Comando AceptarCotizacion: el agregado se RECONSTRUYE desde el event
store (event sourcing) antes de aplicar la operación."""
from dataclasses import dataclass
import uuid

from cotizaciones.seedwork.aplicacion.comandos import Comando
from cotizaciones.seedwork.aplicacion.comandos import ejecutar_commando as comando
from cotizaciones.seedwork.infraestructura.uow import UnidadTrabajoPuerto
from .base import ComandoCotizacionBaseHandler
from ...dominio.excepciones import CotizacionNoExiste
from ...dominio.repositorios import RepositorioCotizaciones, RepositorioEventosCotizaciones


@dataclass
class AceptarCotizacion(Comando):
    id_cotizacion: str


class AceptarCotizacionHandler(ComandoCotizacionBaseHandler):

    def handle(self, comando: AceptarCotizacion) -> str:
        repositorio = self.fabrica_repositorio.crear_objeto(RepositorioCotizaciones)
        repositorio_eventos = self.fabrica_repositorio.crear_objeto(RepositorioEventosCotizaciones)

        cotizacion = repositorio_eventos.reconstruir(uuid.UUID(comando.id_cotizacion))
        if cotizacion is None:
            raise CotizacionNoExiste(comando.id_cotizacion)

        cotizacion.aceptar_cotizacion()                 # reglas + evento CotizacionAceptada

        UnidadTrabajoPuerto.registrar_batch(
            repositorio.actualizar, cotizacion,          # actualiza la proyección
            repositorio_eventos_func=repositorio_eventos.agregar)   # append al store
        UnidadTrabajoPuerto.commit()
        return cotizacion.estado.value


@comando.register(AceptarCotizacion)
def ejecutar_comando_aceptar_cotizacion(comando: AceptarCotizacion):
    return AceptarCotizacionHandler().handle(comando)
