"""Consumidores del broker (estilo tutorial): suscripción a tópicos de
eventos y comandos. Requiere Pulsar corriendo (docker-compose del curso);
si no está disponible, el hilo termina silenciosamente."""
import logging
import traceback

from cotizaciones.seedwork.infraestructura import utils


def suscribirse_a_eventos(app=None):
    try:
        import pulsar
        cliente = pulsar.Client(f'pulsar://{utils.broker_host()}:6650')
        consumidor = cliente.subscribe(
            'eventos-cotizacion', subscription_name='cotizaciones-sub-eventos')
        while True:
            mensaje = consumidor.receive()
            print(f'Evento recibido: {mensaje.data()}')
            consumidor.acknowledge(mensaje)
    except Exception:
        logging.info('Broker no disponible: consumidor de eventos deshabilitado')
        traceback.print_exc()


def suscribirse_a_comandos(app=None):
    try:
        import pulsar
        cliente = pulsar.Client(f'pulsar://{utils.broker_host()}:6650')
        consumidor = cliente.subscribe(
            'comandos-cotizacion', subscription_name='cotizaciones-sub-comandos')
        while True:
            mensaje = consumidor.receive()
            print(f'Comando recibido: {mensaje.data()}')
            consumidor.acknowledge(mensaje)
    except Exception:
        logging.info('Broker no disponible: consumidor de comandos deshabilitado')
