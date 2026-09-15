"""Comando RetenerPago (lado C de CQS). Llega por el broker: desde el tópico de
comandos `comandos-pago` o traducido de un evento de integración
consumido. Handler IDEMPOTENTE: `id_evento_origen` se registra en la misma
unidad de trabajo que el efecto; una re-entrega se ignora."""
from dataclasses import dataclass

from pagos.seedwork.aplicacion.comandos import Comando
from pagos.seedwork.aplicacion.comandos import ejecutar_commando as comando
from pagos.seedwork.infraestructura.uow import UnidadTrabajoPuerto
from .base import ComandoReservaDePagoBaseHandler
from ..dto import ReservaDePagoDTO
from ..mapeadores import MapeadorReservaDePago
from ...dominio.entidades import ReservaDePago
from ...dominio.repositorios import RepositorioReservas, RepositorioEventosProcesados


@dataclass
class RetenerPago(Comando):
    id_evento_origen: str
    id_cotizacion: str
    id_trabajo: str
    monto: float
    moneda: str
    pais: str = "CO"


class RetenerPagoHandler(ComandoReservaDePagoBaseHandler):

    def handle(self, comando: RetenerPago) -> str:
        repositorio = self.fabrica_repositorio.crear_objeto(RepositorioReservas)
        procesados = self.fabrica_repositorio.crear_objeto(RepositorioEventosProcesados)

        if procesados.ya_procesado(comando.id_evento_origen):
            print(f"[pagos] duplicado {comando.id_evento_origen[:8]} IGNORADO (idempotencia)")
            return "DUPLICADO"

        dto = ReservaDePagoDTO(id_cotizacion=comando.id_cotizacion, id_trabajo=comando.id_trabajo,
                          monto=comando.monto, moneda=comando.moneda, pais=comando.pais)
        entidad: ReservaDePago = self.fabrica.crear_objeto(dto, MapeadorReservaDePago())
        entidad.retener()                       # reglas + evento de dominio

        # efecto + marca de idempotencia en la MISMA transacción
        UnidadTrabajoPuerto.registrar_batch(repositorio.agregar, entidad)
        UnidadTrabajoPuerto.registrar_batch(procesados.agregar, comando.id_evento_origen)
        UnidadTrabajoPuerto.commit()
        return str(entidad.id)


@comando.register(RetenerPago)
def ejecutar_comando_retener_pago(comando: RetenerPago):
    return RetenerPagoHandler().handle(comando)
