"""Entidades del dominio de trabajos. Agregado AgendaDeTrabajo (raíz de agregación):
modelo CRUD — el estado se persiste directamente; las operaciones validan
reglas y agregan eventos de dominio que la UoW publica."""
from dataclasses import dataclass, field

from trabajos.seedwork.dominio.entidades import AgregacionRaiz
from .objetos_valor import Dinero, Estado
from .eventos import TrabajoAgendado, TrabajoRechazado


@dataclass
class AgendaDeTrabajo(AgregacionRaiz):
    id_trabajo: str = field(default=None)
    id_cotizacion: str = field(default=None)
    id_pago: str = field(default=None)
    pais: str = field(default="CO")
    id_proveedor: str = field(default=None)
    estado: Estado = field(default=Estado.AGENDADO)

    def agendar(self):
        """Confirma el trabajo (núcleo del negocio) con pago garantizado."""
        self.estado = Estado.AGENDADO
        self.agregar_evento(TrabajoAgendado(
            id_agenda=str(self.id), id_trabajo=self.id_trabajo, id_cotizacion=self.id_cotizacion,
            id_pago=self.id_pago, pais=self.pais))

    def rechazar(self, motivo: str):
        """El trabajo no se puede ejecutar: se registra el rechazo y se emite el
        evento que hará compensar la transacción larga."""
        self.estado = Estado.RECHAZADO
        self.agregar_evento(TrabajoRechazado(
            id_trabajo=self.id_trabajo, id_cotizacion=self.id_cotizacion,
            id_pago=self.id_pago, motivo=motivo))
