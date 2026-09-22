"""Comando de COMPENSACIÓN RevertirPago: libera el escrow de una cotización.
Lo publica el orquestador de la saga cuando un paso posterior falla."""
from dataclasses import dataclass

from pagos.seedwork.aplicacion.comandos import Comando
from pagos.seedwork.aplicacion.comandos import ejecutar_commando as comando
from pagos.seedwork.infraestructura.uow import UnidadTrabajoPuerto
from .base import ComandoReservaDePagoBaseHandler
from ...dominio.repositorios import RepositorioReservas, RepositorioEventosProcesados


@dataclass
class RevertirPago(Comando):
    id_evento_origen: str
    id_cotizacion: str
    motivo: str = "compensacion de saga"


class RevertirPagoHandler(ComandoReservaDePagoBaseHandler):

    def handle(self, comando: RevertirPago) -> str:
        repositorio = self.fabrica_repositorio.crear_objeto(RepositorioReservas)
        procesados = self.fabrica_repositorio.crear_objeto(RepositorioEventosProcesados)
        if procesados.ya_procesado(comando.id_evento_origen):
            print(f"[pagos] duplicado {comando.id_evento_origen[:8]} IGNORADO (idempotencia)")
            return "DUPLICADO"
        reserva = repositorio.obtener_por_cotizacion(comando.id_cotizacion)
        if reserva is None:
            print(f"[pagos] RevertirPago: no hay reserva para {comando.id_cotizacion[:8]} (nada que compensar)")
            return "SIN_RESERVA"
        reserva.revertir(comando.motivo)                     # regla + evento PagoRevertido
        UnidadTrabajoPuerto.registrar_batch(repositorio.actualizar, reserva)
        UnidadTrabajoPuerto.registrar_batch(procesados.agregar, comando.id_evento_origen)
        UnidadTrabajoPuerto.commit()
        return str(reserva.id)


@comando.register(RevertirPago)
def ejecutar_comando_revertir_pago(comando: RevertirPago):
    return RevertirPagoHandler().handle(comando)
