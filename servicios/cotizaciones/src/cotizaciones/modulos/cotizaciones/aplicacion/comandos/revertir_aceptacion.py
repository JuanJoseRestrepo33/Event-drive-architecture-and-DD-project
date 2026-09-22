"""Comando de COMPENSACIÓN RevertirAceptacion: la saga falló aguas abajo
(p. ej. el trabajo no pudo agendarse). El agregado vuelve a EMITIDA mediante
un evento nuevo en el event store (nunca se borra historia)."""
from dataclasses import dataclass
import uuid

from cotizaciones.seedwork.aplicacion.comandos import Comando
from cotizaciones.seedwork.aplicacion.comandos import ejecutar_commando as comando
from cotizaciones.seedwork.infraestructura.uow import UnidadTrabajoPuerto
from .base import ComandoCotizacionBaseHandler
from ...dominio.excepciones import CotizacionNoExiste
from ...dominio.repositorios import RepositorioCotizaciones, RepositorioEventosCotizaciones


@dataclass
class RevertirAceptacion(Comando):
    id_cotizacion: str
    motivo: str = "compensacion de saga"


class RevertirAceptacionHandler(ComandoCotizacionBaseHandler):

    def handle(self, comando: RevertirAceptacion) -> str:
        repositorio = self.fabrica_repositorio.crear_objeto(RepositorioCotizaciones)
        repositorio_eventos = self.fabrica_repositorio.crear_objeto(RepositorioEventosCotizaciones)
        cotizacion = repositorio_eventos.reconstruir(uuid.UUID(comando.id_cotizacion))
        if cotizacion is None:
            raise CotizacionNoExiste(comando.id_cotizacion)
        cotizacion.revertir_aceptacion(comando.motivo)       # regla + evento CotizacionRevertida
        UnidadTrabajoPuerto.registrar_batch(
            repositorio.actualizar, cotizacion,
            repositorio_eventos_func=repositorio_eventos.agregar)
        UnidadTrabajoPuerto.commit()
        return cotizacion.estado.value


@comando.register(RevertirAceptacion)
def ejecutar_comando_revertir_aceptacion(comando: RevertirAceptacion):
    return RevertirAceptacionHandler().handle(comando)
