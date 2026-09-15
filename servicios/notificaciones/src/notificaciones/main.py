"""Punto de entrada: PYTHONPATH=src python src/notificaciones/main.py (puerto 5003)."""
from notificaciones.api import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
