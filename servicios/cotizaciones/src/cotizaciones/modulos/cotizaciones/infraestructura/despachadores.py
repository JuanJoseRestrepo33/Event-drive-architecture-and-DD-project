"""Despachador: publica eventos de INTEGRACIÓN al broker a través del
puerto del seedwork (Pulsar o archivo según BROKER)."""
from dataclasses import asdict

from cotizaciones.seedwork.infraestructura.broker import broker
from .mapeadores import MapeadorEventosCotizacion


class Despachador:
    def __init__(self):
        self.mapeador = MapeadorEventosCotizacion()
        self.broker = broker()

    def publicar_evento(self, evento, topico):
        evento_integracion = self.mapeador.entidad_a_dto(evento)
        mensaje = asdict(evento_integracion)
        mensaje["class"] = "evento"
        mensaje["service_source"] = "cotizaciones"
        self.broker.publicar(topico, mensaje)
        print(f"[cotizaciones] EVENTO {mensaje['type']} {mensaje['specversion']} "
              f"publicado en '{topico}'")
