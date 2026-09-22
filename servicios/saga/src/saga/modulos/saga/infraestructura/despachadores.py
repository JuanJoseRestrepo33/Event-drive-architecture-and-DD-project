"""Despachador de COMANDOS del orquestador hacia los tópicos de comandos de
cada servicio participante (por el puerto del broker)."""
import time
import uuid

from saga.seedwork.infraestructura.broker import broker


class DespachadorComandos:
    def __init__(self):
        self.broker = broker()

    def publicar_comando(self, id_saga: str, tipo: str, topico: str, data: dict, es_compensacion=False):
        mensaje = {"id": str(uuid.uuid4()), "time": int(time.time() * 1000), "specversion": "v1",
                   "type": tipo, "class": "comando", "service_source": "saga",
                   "id_saga": id_saga, "data": data}
        self.broker.publicar(topico, mensaje)
        print(f"[saga] {'COMPENSACIÓN' if es_compensacion else 'COMANDO'} {tipo} → '{topico}' "
              f"(saga {id_saga[:8]}…)")
