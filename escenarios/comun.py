"""Utilidades comunes de los escenarios."""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servicios", "cotizaciones", "src"))
import contratos  # noqa: E402  (factorías del cliente)
from cotizaciones.seedwork.infraestructura import broker as broker_mod  # noqa: E402  (puerto + adaptadores)

COTIZACIONES = os.getenv("URL_COTIZACIONES", "http://localhost:5001")
PAGOS = os.getenv("URL_PAGOS", "http://localhost:5002")
NOTIFICACIONES = os.getenv("URL_NOTIFICACIONES", "http://localhost:5003")


def get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read())


def esperar(condicion, timeout=60, cada=0.5, descripcion=""):
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            if condicion():
                return time.time() - inicio
        except Exception:
            pass
        time.sleep(cada)
    raise TimeoutError(f"Timeout esperando: {descripcion}")
