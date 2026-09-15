"""Punto de entrada: PYTHONPATH=src python src/trabajos/main.py (puerto 5004)."""
from trabajos.api import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)
