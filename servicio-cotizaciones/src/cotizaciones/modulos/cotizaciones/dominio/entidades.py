"""Entidades del dominio de cotizaciones.

Ciclo de vida del agregado (patrón del tutorial):
  fábrica construye -> crear_cotizacion(agrega CotizacionCreada) ->
  UoW registra batch (señal CotizacionCreadaDominio + event store) ->
  commit (señal CotizacionCreadaIntegracion -> broker).
"""
from dataclasses import dataclass, field
from datetime import datetime

from cotizaciones.seedwork.dominio.entidades import Entidad, AgregacionRaiz
from .objetos_valor import Dinero, Alcance, Vigencia, EstadoCotizacion
from .eventos import CotizacionCreada, VisitaSolicitada, CotizacionAceptada
from .reglas import SoloEmitidaSePuedeAceptar, NoSePuedeAceptarVencida


@dataclass
class SolicitudDeVisita(Entidad):
    """Entidad interna del agregado: vive y muere con la cotización."""
    fecha_propuesta: datetime = None
    confirmada: bool = False


@dataclass
class Cotizacion(AgregacionRaiz):
    id_trabajo: str = field(default=None)
    id_proveedor: str = field(default=None)
    valor: Dinero = field(default=None)
    alcance: Alcance = field(default=None)
    vigencia: Vigencia = field(default=None)
    estado: EstadoCotizacion = field(default=EstadoCotizacion.EMITIDA)
    visitas: list[SolicitudDeVisita] = field(default_factory=list)

    def crear_cotizacion(self, cotizacion):
        self.id_trabajo = cotizacion.id_trabajo
        self.id_proveedor = cotizacion.id_proveedor
        self.valor = cotizacion.valor
        self.alcance = cotizacion.alcance
        self.vigencia = cotizacion.vigencia
        self.estado = EstadoCotizacion.EMITIDA
        self.agregar_evento(CotizacionCreada(
            id_cotizacion=self.id, id_trabajo=self.id_trabajo,
            id_proveedor=self.id_proveedor, monto=self.valor.monto,
            moneda=self.valor.moneda.value))

    def solicitar_visita(self, fecha_propuesta: datetime):
        visita = SolicitudDeVisita()
        visita.fecha_propuesta = fecha_propuesta
        self.visitas.append(visita)
        self.agregar_evento(VisitaSolicitada(
            id_cotizacion=self.id, fecha_propuesta=fecha_propuesta.isoformat()))

    def aceptar_cotizacion(self, momento: datetime = None):
        momento = momento or datetime.now()
        self.validar_regla(SoloEmitidaSePuedeAceptar(self.estado))
        self.validar_regla(NoSePuedeAceptarVencida(self.vigencia, momento))
        self.estado = EstadoCotizacion.ACEPTADA
        self.agregar_evento(CotizacionAceptada(
            id_cotizacion=self.id, id_trabajo=self.id_trabajo,
            id_proveedor=self.id_proveedor, monto=self.valor.monto,
            moneda=self.valor.moneda.value))
