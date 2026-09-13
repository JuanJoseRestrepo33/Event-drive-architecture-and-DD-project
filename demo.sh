#!/usr/bin/env bash
# Demo de sustentación: muestra el evento viajando de punta a punta.
# Uso: bash demo.sh   (requiere: pip install -r requirements.txt)
# Compatible con Linux, Mac y Windows (Git Bash).
set -e

# --- detectar el intérprete de Python (en Windows se llama 'python';
#     'python3' suele ser el alias falso de la Microsoft Store)
PY=python3
if ! "$PY" -c "pass" >/dev/null 2>&1; then
  PY=python
fi
echo "==> usando intérprete: $PY ($($PY --version 2>&1))"

export PYTHONPATH=src
# pwd -W entrega la ruta estilo C:/... en Git Bash (Windows); en Linux/Mac usa pwd
BASE="$(pwd -W 2>/dev/null || pwd)"
export DB_URL="sqlite:///$BASE/demo.db"
export TOPICO_LOG="$BASE/demo_topico.log"
rm -f demo.db demo_topico.log servidor.out 2>/dev/null || true

echo "==> 1. Levantando el servicio en el puerto 5000..."
"$PY" src/cotizaciones/main.py > servidor.out 2>&1 &
PID=$!
sleep 3

echo "==> 2. COMANDO CrearCotizacion (POST /cotizaciones)"
ID=$(curl -s -X POST localhost:5000/cotizaciones -H 'Content-Type: application/json' -d '{
  "id_trabajo":"TRB-001","id_proveedor":"PRV-9","monto":250000,"moneda":"COP",
  "categoria":"plomeria","descripcion":"cambio de tuberia",
  "vigencia_desde":"2026-01-01T00:00:00","vigencia_hasta":"2030-01-01T00:00:00"}' \
  | "$PY" -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "    id de la cotización: $ID"

echo "==> 3. QUERY (GET /cotizaciones/$ID)"
curl -s localhost:5000/cotizaciones/$ID | "$PY" -m json.tool | head -6

echo "==> 4. COMANDO AceptarCotizacion (dispara el evento que cruza módulos)"
curl -s -X POST localhost:5000/cotizaciones/$ID/aceptar | "$PY" -m json.tool

sleep 1
echo ""
echo "==> 5. TRAZAS del servidor (el evento viajando):"
grep -E "\[uow\]|\[pagos\]|\[despachador\]" servidor.out || true

echo ""
echo "==> 6. EVENT STORE (tabla eventos_cotizacion):"
"$PY" -c "
import sqlite3
con = sqlite3.connect('demo.db')
for fila in con.execute('select tipo_evento, version, substr(contenido,1,80) from eventos_cotizacion'):
    print('   ', fila)
con.close()"

echo ""
echo "==> 7. RESERVA DE PAGO creada por el módulo pagos (misma transacción):"
"$PY" -c "
import sqlite3
con = sqlite3.connect('demo.db')
for fila in con.execute('select id_cotizacion, monto, moneda, estado from reservas_pago'):
    print('   ', fila)
con.close()"

echo ""
echo "==> 8. TÓPICO eventos-cotizacion (eventos de INTEGRACIÓN v1 publicados):"
cat demo_topico.log

kill $PID 2>/dev/null || true
echo ""
echo "==> demo terminada"
