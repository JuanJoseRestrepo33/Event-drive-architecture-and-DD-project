"""Reglas de negocio del dominio de cotizaciones"""
from datetime import datetime

from cotizaciones.seedwork.dominio.reglas import ReglaNegocio
from .objetos_valor import Dinero, Vigencia, EstadoCotizacion


class MontoDebeSerPositivo(ReglaNegocio):
    def __init__(self, valor: Dinero, mensaje='El monto de la cotización debe ser mayor que cero'):
        super().__init__(mensaje)
        self.valor = valor

    def es_valido(self) -> bool:
        return self.valor is not None and self.valor.monto > 0


class VigenciaDebeSerValida(ReglaNegocio):
    def __init__(self, vigencia: Vigencia, mensaje='La vigencia debe tener un rango válido (desde < hasta)'):
        super().__init__(mensaje)
        self.vigencia = vigencia

    def es_valido(self) -> bool:
        return self.vigencia is not None and self.vigencia.desde < self.vigencia.hasta


class SoloEmitidaSePuedeAceptar(ReglaNegocio):
    def __init__(self, estado, mensaje='Solo una cotización EMITIDA puede aceptarse'):
        super().__init__(mensaje)
        self.estado = estado

    def es_valido(self) -> bool:
        return self.estado == EstadoCotizacion.EMITIDA


class NoSePuedeAceptarVencida(ReglaNegocio):
    def __init__(self, vigencia: Vigencia, momento: datetime, mensaje='La cotización está vencida: no puede aceptarse'):
        super().__init__(mensaje)
        self.vigencia = vigencia
        self.momento = momento

    def es_valido(self) -> bool:
        return self.vigencia.vigente(self.momento)
