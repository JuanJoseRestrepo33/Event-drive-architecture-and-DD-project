#!/usr/bin/env bash
# E7 en Modo A (Docker + Pulsar) desde cualquier host (Windows/Git Bash, Mac, Linux, VM de GCP):
# el host para/arranca pagos; el escenario corre en el contenedor `escenarios`.
# Uso (desde la raíz del repo, con `docker compose up -d` ya corriendo):
#   bash escenarios/e7_docker.sh          (o `sudo bash ...` si docker requiere sudo)
set -e
cd "$(dirname "$0")/.."
# si el usuario no puede hablar con el daemon, usar sudo automáticamente (VM de GCP)
DC="docker compose"
if ! docker info > /dev/null 2>&1; then DC="sudo docker compose"; fi
mkdir -p escenarios/estado
$DC build -q escenarios
echo "== E7: deteniendo pagos =="
$DC stop pagos
$DC run --rm escenarios python escenario_e7_disponibilidad.py --fase caida
echo "== E7: rearrancando pagos =="
$DC start pagos
$DC run --rm escenarios python escenario_e7_disponibilidad.py --fase recuperacion
