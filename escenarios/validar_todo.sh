#!/usr/bin/env bash
# Validación integrada (Modo B, sin Docker): levanta los 4 microservicios con el
# broker de archivos, corre los 3 escenarios de calidad y apaga todo.
# Uso: bash escenarios/validar_todo.sh        (desde la raíz del repo; Linux/Mac/WSL)
set -u
cd "$(dirname "$0")/.."
RAIZ="$PWD"
PY=python3; "$PY" -c "pass" >/dev/null 2>&1 || PY=python

# higiene: servicios viejos (incluido un pagos relanzado por un E7 anterior) y estado previo
pkill -f 'src/[a-z]*/main\.py$' >/dev/null 2>&1 || true
for p in 5001 5002 5003 5004; do fuser -k -TERM $p/tcp >/dev/null 2>&1 || true; done
sleep 1
rm -rf broker_dev servicios/*/src/*/api/*.db servicios/*/src/*/*.pid
export BROKER=archivo BROKER_DIR="$RAIZ/broker_dev"
mkdir -p /tmp/hda_logs

arrancar() {  # nombre -> proceso python REAL en /tmp/<nombre>.pid (exec: el subshell se vuelve python)
  ( cd "servicios/$1" && PYTHONPATH=src exec "$PY" "src/$1/main.py" > "/tmp/hda_logs/$1.log" 2>&1 ) &
  echo $! > "/tmp/$1.pid"
}
arrancar cotizaciones; arrancar pagos; arrancar notificaciones; arrancar trabajos
sleep 4
for p in 5001 5002 5003 5004; do curl -s "localhost:$p/health"; echo; done

cd escenarios
N=${N:-30}        timeout 90  "$PY" escenario_e1_escalabilidad.py;   E1=$?
                  timeout 40  "$PY" escenario_e6_modificabilidad.py; E6=$?
N_CAIDA=${N_CAIDA:-15} timeout 150 "$PY" escenario_e7_disponibilidad.py; E7=$?

# apagar (incluido el pagos relanzado por E7: escribe su pid en servicios/pagos/pagos.pid)
kill $(cat /tmp/cotizaciones.pid /tmp/notificaciones.pid /tmp/trabajos.pid "$RAIZ/servicios/pagos/src/pagos/pagos.pid") 2>/dev/null
sleep 1; pkill -f 'src/[a-z]*/main\.py$' >/dev/null 2>&1 || true
echo "=== RESULTADO: E1=$( [ $E1 = 0 ] && echo CUMPLIDO || echo FALLIDO )  E6=$( [ $E6 = 0 ] && echo CUMPLIDO || echo FALLIDO )  E7=$( [ $E7 = 0 ] && echo CUMPLIDO || echo FALLIDO ) ==="
echo "logs de los servicios en /tmp/hda_logs/"
