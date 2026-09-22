"""Comando IniciarSagaAceptacion: arranca la transacción larga para una
cotización. Llega por el tópico `comandos-saga` (lo publica el BFF)."""
from dataclasses import dataclass, field

from saga.seedwork.aplicacion.comandos import Comando
from saga.seedwork.aplicacion.comandos import ejecutar_commando as comando
from .base import ComandoSagaBaseHandler
from ...dominio.entidades import Saga


@dataclass
class IniciarSagaAceptacion(Comando):
    id_mensaje: str
    id_cotizacion: str
    id_saga: str = None
    datos: dict = field(default_factory=dict)


class IniciarSagaAceptacionHandler(ComandoSagaBaseHandler):

    def handle(self, comando: IniciarSagaAceptacion) -> str:
        if self.procesados.ya_procesado(comando.id_mensaje):
            print(f"[saga] duplicado {comando.id_mensaje[:8]} IGNORADO (idempotencia)")
            return "DUPLICADO"
        existente = self.sagas.obtener_por_cotizacion(comando.id_cotizacion)
        if existente is not None:
            print(f"[saga] ya existe una saga para la cotización {comando.id_cotizacion[:8]}… ({existente.estado.value})")
            return str(existente.id)
        saga = Saga()
        if comando.id_saga:
            import uuid
            saga._id = uuid.UUID(comando.id_saga)
        saga.iniciar(comando.id_cotizacion, comando.datos)
        self.persistir_y_despachar(saga, nueva=True, id_mensaje_origen=comando.id_mensaje)
        print(f"[saga] SAGA {str(saga.id)[:8]}… INICIADA para cotización {comando.id_cotizacion[:8]}…")
        return str(saga.id)


@comando.register(IniciarSagaAceptacion)
def ejecutar_iniciar_saga(comando: IniciarSagaAceptacion):
    return IniciarSagaAceptacionHandler().handle(comando)
