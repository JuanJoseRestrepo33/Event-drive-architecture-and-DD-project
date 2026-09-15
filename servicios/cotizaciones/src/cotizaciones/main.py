"""Punto de entrada: PYTHONPATH=src python src/cotizaciones/main.py (puerto 5001)."""
from cotizaciones.api import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
