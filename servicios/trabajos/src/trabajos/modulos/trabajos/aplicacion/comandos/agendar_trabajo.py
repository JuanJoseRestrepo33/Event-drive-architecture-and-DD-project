"""Comando AgendarTrabajo (lado C de CQS). Llega por el broker: desde el tópico de
comandos `comandos-trabajo` o traducido de un evento de integración
consumido. Handler IDEMPOTENTE: `id_evento_origen` se registra en la misma
unidad de trabajo que el efecto; una re-entrega se ignora."""
from dataclasses import dataclass
import os

from trabajos.seedwork.aplicacion.comandos import Comando
from trabajos.seedwork.aplicacion.comandos import ejecutar_commando as comando
from trabajos.seedwork.infraestructura.uow import UnidadTrabajoPuerto
from .base import ComandoAgendaDeTrabajoBaseHandler
from ..dto import AgendaDeTrabajoDTO
from ..mapeadores import MapeadorAgendaDeTrabajo
from ...dominio.entidades import AgendaDeTrabajo
from ...dominio.repositorios import RepositorioAgendas, RepositorioEventosProcesados
from ...dominio.reglas import ProveedorDebeTenerDisponibilidad


@dataclass
class AgendarTrabajo(Comando):
    id_evento_origen: str
    id_trabajo: str
    id_cotizacion: str
    id_pago: str
    pais: str = "CO"
    id_proveedor: str = ""


class AgendarTrabajoHandler(ComandoAgendaDeTrabajoBaseHandler):

    def handle(self, comando: AgendarTrabajo) -> str:
        repositorio = self.fabrica_repositorio.crear_objeto(RepositorioAgendas)
        procesados = self.fabrica_repositorio.crear_objeto(RepositorioEventosProcesados)

        if procesados.ya_procesado(comando.id_evento_origen):
            print(f"[trabajos] duplicado {comando.id_evento_origen[:8]} IGNORADO (idempotencia)")
            return "DUPLICADO"

        dto = AgendaDeTrabajoDTO(id_trabajo=comando.id_trabajo, id_cotizacion=comando.id_cotizacion,
                          id_pago=comando.id_pago, pais=comando.pais, id_proveedor=comando.id_proveedor)
        entidad: AgendaDeTrabajo = self.fabrica.crear_objeto(dto, MapeadorAgendaDeTrabajo())

        # Regla de negocio que puede FALLAR la transacción larga: disponibilidad del
        # proveedor. Si no la cumple, el agregado se registra como RECHAZADO y emite
        # TrabajoRechazado (la saga compensará pago y aceptación).
        sin_cupo = set(os.getenv("PROVEEDORES_SIN_CUPO", "PRV-SIN-CUPO").split(","))
        regla = ProveedorDebeTenerDisponibilidad(comando.id_proveedor, sin_cupo)
        if regla.es_valido():
            entidad.agendar()                   # reglas + evento TrabajoAgendado
        else:
            entidad.rechazar(regla.mensaje_error())     # evento TrabajoRechazado

        # efecto + marca de idempotencia en la MISMA transacción
        UnidadTrabajoPuerto.registrar_batch(repositorio.agregar, entidad)
        UnidadTrabajoPuerto.registrar_batch(procesados.agregar, comando.id_evento_origen)
        UnidadTrabajoPuerto.commit()
        return str(entidad.id)


@comando.register(AgendarTrabajo)
def ejecutar_comando_agendar_trabajo(comando: AgendarTrabajo):
    return AgendarTrabajoHandler().handle(comando)
