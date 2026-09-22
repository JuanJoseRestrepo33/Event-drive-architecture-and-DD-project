"""Punto de entrada del BFF: PYTHONPATH=src python src/bff/main.py (puerto 5000)."""
from bff.api import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
