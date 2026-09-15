"""Comando CrearCotizacion (lado C de CQS). Llega por el tópico
comandos-cotizacion (consumidor) — no por HTTP."""
from dataclasses import dataclass

from cotizaciones.seedwork.aplicacion.comandos import Comando
from cotizaciones.seedwork.aplicacion.comandos import ejecutar_commando as comando
from cotizaciones.seedwork.infraestructura.uow import UnidadTrabajoPuerto
from .base import ComandoCotizacionBaseHandler
from ..dto import CotizacionDTO
from ..mapeadores import MapeadorCotizacion
from ...dominio.entidades import Cotizacion
from ...dominio.repositorios import RepositorioCotizaciones, RepositorioEventosCotizaciones


@dataclass
class CrearCotizacion(Comando):
    id_trabajo: str
    id_proveedor: str
    monto: float
    moneda: str
    pais: str = "CO"


class CrearCotizacionHandler(ComandoCotizacionBaseHandler):

    def handle(self, comando: CrearCotizacion) -> str:
        dto = CotizacionDTO(id_trabajo=comando.id_trabajo, id_proveedor=comando.id_proveedor,
                            monto=comando.monto, moneda=comando.moneda, pais=comando.pais)
        cotizacion: Cotizacion = self.fabrica_cotizaciones.crear_objeto(dto, MapeadorCotizacion())
        cotizacion.crear_cotizacion(cotizacion)          # regla + evento CotizacionCreada

        repositorio = self.fabrica_repositorio.crear_objeto(RepositorioCotizaciones)
        repositorio_eventos = self.fabrica_repositorio.crear_objeto(RepositorioEventosCotizaciones)

        # proyección (read model) + event store, en la MISMA unidad de trabajo
        UnidadTrabajoPuerto.registrar_batch(
            repositorio.agregar, cotizacion,
            repositorio_eventos_func=repositorio_eventos.agregar)
        UnidadTrabajoPuerto.commit()
        return str(cotizacion.id)


@comando.register(CrearCotizacion)
def ejecutar_comando_crear_cotizacion(comando: CrearCotizacion):
    return CrearCotizacionHandler().handle(comando)
