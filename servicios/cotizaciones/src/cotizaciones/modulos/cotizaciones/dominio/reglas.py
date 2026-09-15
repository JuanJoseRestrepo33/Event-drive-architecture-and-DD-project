"""Reglas de negocio del dominio de cotizaciones."""
from cotizaciones.seedwork.dominio.reglas import ReglaNegocio
from .objetos_valor import Dinero, EstadoCotizacion


class MontoDebeSerPositivo(ReglaNegocio):
    def __init__(self, valor: Dinero, mensaje="El monto de la cotización debe ser mayor que cero"):
        super().__init__(mensaje)
        self.valor = valor

    def es_valido(self) -> bool:
        return self.valor is not None and self.valor.monto > 0


class SoloEmitidaSePuedeAceptar(ReglaNegocio):
    def __init__(self, estado, mensaje="Solo una cotización EMITIDA puede aceptarse"):
        super().__init__(mensaje)
        self.estado = estado

    def es_valido(self) -> bool:
        return self.estado == EstadoCotizacion.EMITIDA
