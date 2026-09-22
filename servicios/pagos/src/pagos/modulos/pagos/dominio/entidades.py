"""Entidades del dominio de pagos. Agregado ReservaDePago (raíz de agregación):
modelo CRUD — el estado se persiste directamente; las operaciones validan
reglas y agregan eventos de dominio que la UoW publica."""
from dataclasses import dataclass, field

from pagos.seedwork.dominio.entidades import AgregacionRaiz
from .objetos_valor import Dinero, Estado
from .eventos import PagoRetenido, PagoRevertido
from .reglas import SoloRetenidoSePuedeRevertir


@dataclass
class ReservaDePago(AgregacionRaiz):
    id_cotizacion: str = field(default=None)
    id_trabajo: str = field(default=None)
    valor: Dinero = field(default=None)
    pais: str = field(default="CO")
    estado: Estado = field(default=Estado.RETENIDO)

    def retener(self):
        """Retiene el pago en escrow (garantía para el proveedor)."""
        self.estado = Estado.RETENIDO
        self.agregar_evento(PagoRetenido(
            id_pago=str(self.id), id_cotizacion=self.id_cotizacion, id_trabajo=self.id_trabajo,
            monto=self.valor.monto, moneda=self.valor.moneda.value, pais=self.pais))

    def revertir(self, motivo: str = "compensacion de saga"):
        """COMPENSACIÓN: libera el escrow. Regla: solo si está retenido."""
        self.validar_regla(SoloRetenidoSePuedeRevertir(self.estado))
        self.estado = Estado.LIBERADO
        self.agregar_evento(PagoRevertido(
            id_pago=str(self.id), id_cotizacion=self.id_cotizacion, id_trabajo=self.id_trabajo,
            monto=self.valor.monto, moneda=self.valor.moneda.value, motivo=motivo))
