"""Comando AgendarTrabajo (lado C de CQS). Llega por el broker: desde el tópico de
comandos `comandos-trabajo` o traducido de un evento de integración
consumido. Handler IDEMPOTENTE: `id_evento_origen` se registra en la misma
unidad de trabajo que el efecto; una re-entrega se ignora."""
from dataclasses import dataclass

from trabajos.seedwork.aplicacion.comandos import Comando
from trabajos.seedwork.aplicacion.comandos import ejecutar_commando as comando
from trabajos.seedwork.infraestructura.uow import UnidadTrabajoPuerto
from .base import ComandoAgendaDeTrabajoBaseHandler
from ..dto import AgendaDeTrabajoDTO
from ..mapeadores import MapeadorAgendaDeTrabajo
from ...dominio.entidades import AgendaDeTrabajo
from ...dominio.repositorios import RepositorioAgendas, RepositorioEventosProcesados


@dataclass
class AgendarTrabajo(Comando):
    id_evento_origen: str
    id_trabajo: str
    id_cotizacion: str
    id_pago: str
    pais: str = "CO"


class AgendarTrabajoHandler(ComandoAgendaDeTrabajoBaseHandler):

    def handle(self, comando: AgendarTrabajo) -> str:
        repositorio = self.fabrica_repositorio.crear_objeto(RepositorioAgendas)
        procesados = self.fabrica_repositorio.crear_objeto(RepositorioEventosProcesados)

        if procesados.ya_procesado(comando.id_evento_origen):
            print(f"[trabajos] duplicado {comando.id_evento_origen[:8]} IGNORADO (idempotencia)")
            return "DUPLICADO"

        dto = AgendaDeTrabajoDTO(id_trabajo=comando.id_trabajo, id_cotizacion=comando.id_cotizacion,
                          id_pago=comando.id_pago, pais=comando.pais)
        entidad: AgendaDeTrabajo = self.fabrica.crear_objeto(dto, MapeadorAgendaDeTrabajo())
        entidad.agendar()                       # reglas + evento de dominio

        # efecto + marca de idempotencia en la MISMA transacción
        UnidadTrabajoPuerto.registrar_batch(repositorio.agregar, entidad)
        UnidadTrabajoPuerto.registrar_batch(procesados.agregar, comando.id_evento_origen)
        UnidadTrabajoPuerto.commit()
        return str(entidad.id)


@comando.register(AgendarTrabajo)
def ejecutar_comando_agendar_trabajo(comando: AgendarTrabajo):
    return AgendarTrabajoHandler().handle(comando)
