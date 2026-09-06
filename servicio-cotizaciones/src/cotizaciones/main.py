"""Punto de entrada del servicio (fuera de tests):
    PYTHONPATH=src python src/cotizaciones/main.py"""
from cotizaciones.api import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
