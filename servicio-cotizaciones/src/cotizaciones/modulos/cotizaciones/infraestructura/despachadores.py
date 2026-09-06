"""Despachador de eventos de integración hacia el broker.

En el tutorial el broker es Apache Pulsar (con esquemas Avro). Aquí el
adaptador intenta usar Pulsar si la librería y el broker están disponibles
(BROKER_HOST); si no, degrada a un log JSON-lines que simula el tópico
(eventos_integracion.log) para poder ejecutar y probar el servicio sin
infraestructura. El puerto y el mapeo dominio->integración son los mismos:
cambiar de adaptador NO toca dominio ni aplicación (hexagonal)."""
import json
import os

from cotizaciones.seedwork.infraestructura import utils
from .mapeadores import MapeadorEventosCotizacion


class Despachador:
    def __init__(self):
        self.mapeador = MapeadorEventosCotizacion()

    def _publicar_mensaje_pulsar(self, mensaje, topico):
        import pulsar
        cliente = pulsar.Client(f'pulsar://{utils.broker_host()}:6650')
        publicador = cliente.create_producer(topico)
        publicador.send(json.dumps(
            {'specversion': mensaje.specversion, 'type': mensaje.type,
             'data': mensaje.data.__dict__}).encode('utf-8'))
        cliente.close()

    def _publicar_mensaje_log(self, mensaje, topico):
        with open(os.getenv('TOPICO_LOG', 'eventos_integracion.log'), 'a') as f:
            f.write(json.dumps({'topico': topico, 'id': mensaje.id,
                                'specversion': mensaje.specversion,
                                'type': mensaje.type,
                                'service_name': mensaje.service_name,
                                'data': mensaje.data.__dict__}) + '\n')

    def publicar_evento(self, evento, topico):
        evento_integracion = self.mapeador.entidad_a_dto(evento)
        try:
            self._publicar_mensaje_pulsar(evento_integracion, topico)
        except Exception:
            self._publicar_mensaje_log(evento_integracion, topico)
