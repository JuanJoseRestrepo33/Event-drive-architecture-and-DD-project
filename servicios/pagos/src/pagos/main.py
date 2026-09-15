"""Punto de entrada: PYTHONPATH=src python src/pagos/main.py (puerto 5002)."""
from pagos.api import create_app

app = create_app()

if __name__ == '__main__':
    import os
    # pidfile propio: el escenario E7 (modo dev) lo usa para simular la caída
    with open(os.getenv("PID_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "pagos.pid")), "w") as f:
        f.write(str(os.getpid()))
    app.run(host='0.0.0.0', port=5002)
