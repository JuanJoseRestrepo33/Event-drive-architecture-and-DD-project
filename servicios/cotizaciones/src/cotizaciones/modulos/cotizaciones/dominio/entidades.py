"""Entidades del dominio de cotizaciones.

Agregado Cotizacion con EVENT SOURCING: el estado es una función de sus
eventos (`aplicar`), y `desde_historia` lo reconstruye desde el event
store. Las operaciones validan reglas y AGREGAN eventos que la Unidad de
Trabajo publica (señal `XDominio` pre-commit + event store; señal
`XIntegracion` post-commit -> despachador -> broker).
"""
from dataclasses import dataclass, field
import uuid

from cotizaciones.seedwork.dominio.entidades import AgregacionRaiz
from .objetos_valor import Dinero, Moneda, EstadoCotizacion
from .eventos import CotizacionCreada, CotizacionAceptada, CotizacionRevertida
from .reglas import SoloEmitidaSePuedeAceptar, SoloAceptadaSePuedeRevertir


@dataclass
class Cotizacion(AgregacionRaiz):
    id_trabajo: str = field(default=None)
    id_proveedor: str = field(default=None)
    valor: Dinero = field(default=None)
    pais: str = field(default="CO")
    estado: EstadoCotizacion = field(default=None)
    version: int = field(default=0)

    # ------------------------- comportamiento -------------------------
    def crear_cotizacion(self, cotizacion):
        self.agregar_evento(CotizacionCreada(
            id_cotizacion=self.id, id_trabajo=cotizacion.id_trabajo,
            id_proveedor=cotizacion.id_proveedor, monto=cotizacion.valor.monto,
            moneda=cotizacion.valor.moneda.value, pais=cotizacion.pais))
        self.aplicar(self.eventos[-1])

    def aceptar_cotizacion(self):
        self.validar_regla(SoloEmitidaSePuedeAceptar(self.estado))
        self.agregar_evento(CotizacionAceptada(
            id_cotizacion=self.id, id_trabajo=self.id_trabajo,
            id_proveedor=self.id_proveedor, monto=self.valor.monto,
            moneda=self.valor.moneda.value, pais=self.pais))
        self.aplicar(self.eventos[-1])

    def revertir_aceptacion(self, motivo: str = "compensacion de saga"):
        """COMPENSACIÓN: deshace la aceptación con un evento nuevo (append)."""
        self.validar_regla(SoloAceptadaSePuedeRevertir(self.estado))
        self.agregar_evento(CotizacionRevertida(
            id_cotizacion=self.id, id_trabajo=self.id_trabajo, motivo=motivo))
        self.aplicar(self.eventos[-1])

    # ------------------------- event sourcing -------------------------
    def aplicar(self, evento):
        """El estado SIEMPRE deriva de los eventos (nunca se asigna directo)."""
        if isinstance(evento, CotizacionCreada):
            self._id = evento.id_cotizacion if isinstance(evento.id_cotizacion, uuid.UUID) \
                else uuid.UUID(str(evento.id_cotizacion))
            self.id_trabajo = evento.id_trabajo
            self.id_proveedor = evento.id_proveedor
            self.valor = Dinero(evento.monto, Moneda(evento.moneda))
            self.pais = evento.pais or "CO"
            self.estado = EstadoCotizacion.EMITIDA
        elif isinstance(evento, CotizacionAceptada):
            self.estado = EstadoCotizacion.ACEPTADA
        elif isinstance(evento, CotizacionRevertida):
            self.estado = EstadoCotizacion.EMITIDA
        self.version += 1

    @classmethod
    def desde_historia(cls, eventos: list) -> "Cotizacion":
        cotizacion = cls()
        for evento in eventos:
            cotizacion.aplicar(evento)
        cotizacion.limpiar_eventos()      # la historia no se re-publica
        return cotizacion
