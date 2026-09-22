"""Comando interno ProcesarEventoDeSaga: un evento de integración de un
servicio participante llegó; la saga correspondiente avanza, termina o
compensa. Idempotente por id de evento."""
from dataclasses import dataclass, field

from saga.seedwork.aplicacion.comandos import Comando
from saga.seedwork.aplicacion.comandos import ejecutar_commando as comando
from .base import ComandoSagaBaseHandler
from ...dominio.entidades import SagaTerminada


@dataclass
class ProcesarEventoDeSaga(Comando):
    id_evento: str
    tipo_evento: str
    id_cotizacion: str
    data: dict = field(default_factory=dict)


class ProcesarEventoDeSagaHandler(ComandoSagaBaseHandler):

    def handle(self, comando: ProcesarEventoDeSaga) -> str:
        if self.procesados.ya_procesado(comando.id_evento):
            print(f"[saga] evento duplicado {comando.id_evento[:8]} IGNORADO (idempotencia)")
            return "DUPLICADO"
        saga = self.sagas.obtener_por_cotizacion(comando.id_cotizacion)
        if saga is None:
            return "SIN_SAGA"          # evento de una cotización que no está en una transacción larga
        try:
            saga.aplicar_evento(comando.tipo_evento, comando.data, comando.id_evento)
        except SagaTerminada as e:
            print(f"[saga] {e}")
            return "TERMINADA"
        self.persistir_y_despachar(saga, nueva=False, id_mensaje_origen=comando.id_evento)
        print(f"[saga] saga {str(saga.id)[:8]}… ← {comando.tipo_evento} ⇒ estado {saga.estado.value}"
              f"{' · paso ' + saga.paso_actual if saga.paso_actual else ''}")
        return saga.estado.value


@comando.register(ProcesarEventoDeSaga)
def ejecutar_procesar_evento(comando: ProcesarEventoDeSaga):
    return ProcesarEventoDeSagaHandler().handle(comando)
