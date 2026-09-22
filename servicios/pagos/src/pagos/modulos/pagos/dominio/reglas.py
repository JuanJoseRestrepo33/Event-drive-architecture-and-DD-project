"""Reglas de negocio del dominio de pagos."""
from pagos.seedwork.dominio.reglas import ReglaNegocio
from .objetos_valor import Dinero


class MontoDebeSerPositivo(ReglaNegocio):
    def __init__(self, valor: Dinero, mensaje="No se retiene un pago con monto <= 0"):
        super().__init__(mensaje)
        self.valor = valor

    def es_valido(self) -> bool:
        return self.valor is not None and self.valor.monto > 0


class SoloRetenidoSePuedeRevertir(ReglaNegocio):
    def __init__(self, estado, mensaje="Solo un pago RETENIDO puede revertirse"):
        super().__init__(mensaje)
        self.estado = estado

    def es_valido(self) -> bool:
        return str(getattr(self.estado, "value", self.estado)) == "RETENIDO"
