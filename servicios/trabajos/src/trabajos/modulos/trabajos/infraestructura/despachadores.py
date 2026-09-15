"""Despachador: publica el evento de INTEGRACIÓN al broker por el puerto
del seedwork (Pulsar o archivo según BROKER)."""
from dataclasses import asdict

from trabajos.seedwork.infraestructura.broker import broker
from .mapeadores import MapeadorEventosAgendas


class Despachador:
    def __init__(self):
        self.mapeador = MapeadorEventosAgendas()
        self.broker = broker()

    def publicar_evento(self, evento, topico):
        mensaje = asdict(self.mapeador.entidad_a_dto(evento))
        mensaje["class"] = "evento"
        mensaje["service_source"] = "trabajos"
        self.broker.publicar(topico, mensaje)
        print(f"[trabajos] EVENTO {mensaje['type']} {mensaje['specversion']} publicado en '{topico}'")
