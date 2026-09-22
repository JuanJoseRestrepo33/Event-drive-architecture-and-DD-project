#!/usr/bin/env bash
# Instala Docker + Compose en una VM Ubuntu 22.04 de GCP y levanta la POC.
# Uso (dentro de la VM, ya clonado el repo):
#   bash gcp/instalar-vm.sh
set -euo pipefail

echo "== 1/4 Instalando Docker Engine + Compose v2 =="
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -qq
sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker "$USER"
echo "   docker $(sudo docker --version | cut -d' ' -f3) · compose $(sudo docker compose version --short)"

echo "== 2/4 Levantando Pulsar + 4 microservicios + orquestador de sagas + BFF =="
cd "$(dirname "$0")/.."
sudo docker compose up --build -d
echo "   esperando healthcheck de Pulsar y arranque de los servicios..."
for i in $(seq 1 30); do
  if curl -sf localhost:5000/bff/health > /dev/null 2>&1; then break; fi
  sleep 5
done

echo "== 3/4 Construyendo el contenedor de escenarios =="
sudo docker compose build -q escenarios

echo "== 4/4 Estado =="
sudo docker compose ps
curl -s localhost:5000/bff/health; echo
IP=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip || echo "<IP_PUBLICA>")
echo
echo "Listo. Desde su máquina:  curl http://$IP:5000/bff/health"
echo "Postman: environment HdA-gcp con base_url = http://$IP:5000"
