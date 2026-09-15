"""PUERTO de mensajería (seedwork) con dos ADAPTADORES — inversión de
dependencias: dominio y aplicación no conocen el broker; los despachadores
y consumidores de infraestructura usan este puerto.

- PulsarBroker  (BROKER=pulsar): Apache Pulsar real, exigido por la entrega.
  Requiere BROKER_HOST (docker-compose incluido en el repo).
- ArchivoBroker (BROKER=archivo, default): broker de desarrollo basado en
  archivos (un .jsonl por tópico + offset por suscripción) para correr y
  probar la POC multi-proceso sin Docker. Mismo contrato de mensajes.

`broker()` devuelve UNA instancia por proceso (un solo cliente Pulsar con un
productor por tópico y N consumidores), como recomienda el cliente Pulsar.
Los mensajes viajan como JSON (envelope con specversion, type, data...).
"""
import json
import os
import threading
import time

_instancia = None
_lock = threading.Lock()


def broker():
    global _instancia
    with _lock:
        if _instancia is None:
            _instancia = PulsarBroker() if os.getenv("BROKER", "archivo") == "pulsar" else ArchivoBroker()
        return _instancia


class PulsarBroker:
    def __init__(self):
        import pulsar
        host = os.getenv("BROKER_HOST", "localhost")
        # logger en Warn: sin ruido INFO del cliente en logs y escenarios
        self.cliente = pulsar.Client(
            f"pulsar://{host}:6650",
            logger=pulsar.ConsoleLogger(pulsar.LoggerLevel.Warn))
        self._productores = {}
        self._lock = threading.Lock()

    def _productor(self, topico):
        with self._lock:
            if topico not in self._productores:
                self._productores[topico] = self.cliente.create_producer(topico)
            return self._productores[topico]

    def publicar(self, topico: str, mensaje: dict):
        self._productor(topico).send(json.dumps(mensaje).encode("utf-8"))

    def consumir(self, topico: str, suscripcion: str, handler):
        """Bucle bloqueante: se invoca desde un hilo propio.
        - Shared: varios consumidores de la misma suscripción reparten carga.
        - Earliest: una suscripción nueva arranca desde el primer mensaje
          retenido (no pierde lo publicado antes de suscribirse)."""
        import pulsar
        consumidor = self.cliente.subscribe(
            topico, subscription_name=suscripcion,
            consumer_type=pulsar.ConsumerType.Shared,
            initial_position=pulsar.InitialPosition.Earliest)
        while True:
            msg = consumidor.receive()
            try:
                handler(json.loads(msg.data().decode("utf-8")))
                consumidor.acknowledge(msg)
            except Exception as e:
                print(f"[broker] error procesando, negative-ack: {e}")
                consumidor.negative_acknowledge(msg)


class ArchivoBroker:
    def __init__(self):
        self.dir = os.getenv("BROKER_DIR", os.path.join(os.getcwd(), "broker_dev"))
        os.makedirs(self.dir, exist_ok=True)

    def _ruta(self, topico):
        return os.path.join(self.dir, topico + ".jsonl")

    def publicar(self, topico: str, mensaje: dict):
        with open(self._ruta(topico), "a", encoding="utf-8") as f:
            f.write(json.dumps(mensaje) + "\n")

    def consumir(self, topico: str, suscripcion: str, handler):
        off_path = os.path.join(self.dir, f"{topico}.{suscripcion}.offset")
        offset = int(open(off_path).read()) if os.path.exists(off_path) else 0
        while True:
            ruta = self._ruta(topico)
            lineas = open(ruta, encoding="utf-8").readlines() if os.path.exists(ruta) else []
            while offset < len(lineas):
                try:
                    handler(json.loads(lineas[offset]))
                except Exception as e:
                    print(f"[broker] error procesando offset {offset}: {e}")
                offset += 1
                with open(off_path, "w") as f:
                    f.write(str(offset))
            time.sleep(0.15)
