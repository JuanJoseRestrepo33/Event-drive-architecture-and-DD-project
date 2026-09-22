"""Punto de entrada del orquestador: PYTHONPATH=src python src/saga/main.py (puerto 5005)."""
from saga.api import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)
