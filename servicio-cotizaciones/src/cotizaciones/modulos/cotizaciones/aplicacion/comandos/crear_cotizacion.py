"""Comando CrearCotizacion (lado C de CQS, estilo del tutorial)."""
from dataclasses import dataclass, field

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
    categoria: str
    descripcion: str
    vigencia_desde: str
    vigencia_hasta: str


class CrearCotizacionHandler(ComandoCotizacionBaseHandler):

    def handle(self, comando: CrearCotizacion) -> str:
        cotizacion_dto = CotizacionDTO(
            id_trabajo=comando.id_trabajo, id_proveedor=comando.id_proveedor,
            monto=comando.monto, moneda=comando.moneda,
            categoria=comando.categoria, descripcion=comando.descripcion,
            vigencia_desde=comando.vigencia_desde,
            vigencia_hasta=comando.vigencia_hasta)

        cotizacion: Cotizacion = self.fabrica_cotizaciones.crear_objeto(
            cotizacion_dto, MapeadorCotizacion())
        cotizacion.crear_cotizacion(cotizacion)

        repositorio = self.fabrica_repositorio.crear_objeto(RepositorioCotizaciones)
        repositorio_eventos = self.fabrica_repositorio.crear_objeto(RepositorioEventosCotizaciones)

        UnidadTrabajoPuerto.registrar_batch(
            repositorio.agregar, cotizacion,
            repositorio_eventos_func=repositorio_eventos.agregar)
        UnidadTrabajoPuerto.commit()

        return str(cotizacion.id)


@comando.register(CrearCotizacion)
def ejecutar_comando_crear_cotizacion(comando: CrearCotizacion):
    handler = CrearCotizacionHandler()
    return handler.handle(comando)
