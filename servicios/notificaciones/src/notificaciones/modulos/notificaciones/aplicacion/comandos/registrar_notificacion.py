"""Comando RegistrarNotificacion (lado C de CQS). Llega por el broker: desde el tópico de
comandos `comandos-notificacion` o traducido de un evento de integración
consumido. Handler IDEMPOTENTE: `id_evento_origen` se registra en la misma
unidad de trabajo que el efecto; una re-entrega se ignora."""
from dataclasses import dataclass

from notificaciones.seedwork.aplicacion.comandos import Comando
from notificaciones.seedwork.aplicacion.comandos import ejecutar_commando as comando
from notificaciones.seedwork.infraestructura.uow import UnidadTrabajoPuerto
from .base import ComandoNotificacionBaseHandler
from ..dto import NotificacionDTO
from ..mapeadores import MapeadorNotificacion
from ...dominio.entidades import Notificacion
from ...dominio.repositorios import RepositorioNotificaciones, RepositorioEventosProcesados


@dataclass
class RegistrarNotificacion(Comando):
    id_evento_origen: str
    tipo: str
    version: str
    destinatario: str
    mensaje: str


class RegistrarNotificacionHandler(ComandoNotificacionBaseHandler):

    def handle(self, comando: RegistrarNotificacion) -> str:
        repositorio = self.fabrica_repositorio.crear_objeto(RepositorioNotificaciones)
        procesados = self.fabrica_repositorio.crear_objeto(RepositorioEventosProcesados)

        if procesados.ya_procesado(comando.id_evento_origen):
            print(f"[notificaciones] duplicado {comando.id_evento_origen[:8]} IGNORADO (idempotencia)")
            return "DUPLICADO"

        dto = NotificacionDTO(tipo=comando.tipo, version=comando.version,
                          destinatario=comando.destinatario, mensaje=comando.mensaje)
        entidad: Notificacion = self.fabrica.crear_objeto(dto, MapeadorNotificacion())
        entidad.registrar()                       # reglas + evento de dominio

        # efecto + marca de idempotencia en la MISMA transacción
        UnidadTrabajoPuerto.registrar_batch(repositorio.agregar, entidad)
        UnidadTrabajoPuerto.registrar_batch(procesados.agregar, comando.id_evento_origen)
        UnidadTrabajoPuerto.commit()
        return str(entidad.id)


@comando.register(RegistrarNotificacion)
def ejecutar_comando_registrar_notificacion(comando: RegistrarNotificacion):
    return RegistrarNotificacionHandler().handle(comando)
