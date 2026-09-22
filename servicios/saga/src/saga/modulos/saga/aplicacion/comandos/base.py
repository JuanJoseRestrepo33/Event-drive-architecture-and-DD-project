from saga.seedwork.aplicacion.comandos import ComandoHandler
from saga.seedwork.infraestructura.uow import UnidadTrabajoPuerto
from saga.modulos.saga.infraestructura.fabricas import FabricaRepositorio
from saga.modulos.saga.infraestructura.despachadores import DespachadorComandos
from saga.modulos.saga.dominio.repositorios import RepositorioSagas, RepositorioSagaLog, RepositorioEventosProcesados


class ComandoSagaBaseHandler(ComandoHandler):
    def __init__(self):
        self.fabrica_repositorio = FabricaRepositorio()
        self.sagas = self.fabrica_repositorio.crear_objeto(RepositorioSagas)
        self.log = self.fabrica_repositorio.crear_objeto(RepositorioSagaLog)
        self.procesados = self.fabrica_repositorio.crear_objeto(RepositorioEventosProcesados)
        self.despachador = DespachadorComandos()

    def persistir_y_despachar(self, saga, nueva: bool, id_mensaje_origen: str = None):
        """Guarda estado + SAGA LOG + marca de idempotencia en UNA transacción y,
        tras el commit, publica los comandos que la saga decidió (outbox simple)."""
        pendientes = saga.tomar_comandos_pendientes()
        UnidadTrabajoPuerto.registrar_batch(self.sagas.agregar if nueva else self.sagas.actualizar, saga)
        for entrada in saga.eventos:            # cada evento de dominio = una fila del saga log
            UnidadTrabajoPuerto.registrar_batch(self.log.agregar, entrada)
        if id_mensaje_origen:
            UnidadTrabajoPuerto.registrar_batch(self.procesados.agregar, id_mensaje_origen)
        UnidadTrabajoPuerto.commit()
        saga.limpiar_eventos()
        for c in pendientes:
            self.despachador.publicar_comando(str(saga.id), c.tipo, c.topico, c.data, c.es_compensacion)
