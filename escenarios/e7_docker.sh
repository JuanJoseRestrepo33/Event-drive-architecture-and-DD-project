#!/usr/bin/env bash
# E7 en Modo A (Docker + Pulsar) desde cualquier host, incluido Windows/Git Bash:
# el host para/arranca pagos; el escenario corre en el contenedor `escenarios`.
# Uso (desde la raíz del repo, con `docker compose up -d` ya corriendo):
#   bash escenarios/e7_docker.sh
set -e
cd "$(dirname "$0")/.."
mkdir -p escenarios/estado
docker compose build -q escenarios
echo "== E7: deteniendo pagos =="
docker compose stop pagos
docker compose run --rm escenarios python escenario_e7_disponibilidad.py --fase caida
echo "== E7: rearrancando pagos =="
docker compose start pagos
docker compose run --rm escenarios python escenario_e7_disponibilidad.py --fase recuperacion
