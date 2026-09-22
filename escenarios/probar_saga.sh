#!/usr/bin/env bash
# Demuestra la SAGA orquestada a través del BFF: una transacción EXITOSA y una
# con FALLO + COMPENSACIÓN, y muestra el SAGA LOG por API y por SQL.
# Requiere el sistema arriba (Modo A: docker compose up -d · Modo B: los 6 procesos).
# Uso: bash escenarios/probar_saga.sh [BFF_URL]     (default http://localhost:5000)
set -u
BFF="${1:-http://localhost:5000}"
J="Content-Type: application/json"
PY=python3; "$PY" -c "pass" >/dev/null 2>&1 || PY=python

crear() {  # id_trabajo id_proveedor
  curl -s -X POST "$BFF/bff/cotizaciones" -H "$J" \
    -d "{\"id_trabajo\":\"$1\",\"id_proveedor\":\"$2\",\"monto\":150000,\"moneda\":\"COP\",\"pais\":\"CO\"}" \
    | "$PY" -c 'import sys,json;print(json.load(sys.stdin)["id"])'
}
esperar_saga() {  # id_saga estado_esperado
  for i in $(seq 1 40); do
    E=$(curl -s "$BFF/bff/sagas/$1" | "$PY" -c 'import sys,json;print(json.load(sys.stdin).get("estado",""))' 2>/dev/null)
    [ "$E" = "$2" ] && return 0; sleep 0.5
  done; return 1
}
mostrar_log() {  # id_saga
  curl -s "$BFF/bff/sagas/$1/log" | "$PY" -c '
import sys, json
d = json.load(sys.stdin)
print("   SAGA %s…  estado final: %s" % (d["id_saga"][:8], d["estado"]))
for e in d["log"]:
    print("   %2d  %-22s %-20s %-13s %s" % (e["secuencia"], e["tipo"], e["paso"] or "", e["servicio"] or "", e["mensaje"]))'
}
estado() {  # id_cotizacion
  curl -s "$BFF/bff/cotizaciones/$1/estado" | "$PY" -c '
import sys, json
d = json.load(sys.stdin); s = d.get("saga") or {}
pago = (d.get("pago") or {}).get("estado"); trabajo = (d.get("trabajo") or {}).get("estado")
linea = "   fase=%s · cotizacion=%s (v%s) · pago=%s · trabajo=%s · saga=%s pasos=%s" % (
    d["fase"], d["cotizacion"]["estado"], d["cotizacion"]["version"], pago, trabajo, s.get("estado"), s.get("pasos_completados"))
if s.get("motivo_fallo"): linea += " · motivo=%s" % s["motivo_fallo"]
print(linea)'
}

echo "== salud:"; curl -s "$BFF/bff/health"; echo; echo

echo "==================== 1) TRANSACCIÓN EXITOSA (proveedor PRV-7)"
OK=$(crear TRB-OK-$RANDOM PRV-7); sleep 1.5
R=$(curl -s -X POST "$BFF/bff/cotizaciones/$OK/aceptar"); S_OK=$(echo "$R" | "$PY" -c 'import sys,json;print(json.load(sys.stdin)["id_saga"])')
echo "   POST /bff/cotizaciones/$OK/aceptar -> 202, id_saga=$S_OK"
esperar_saga "$S_OK" COMPLETADA && echo "   saga COMPLETADA" || echo "   (timeout esperando COMPLETADA)"
estado "$OK"; mostrar_log "$S_OK"; echo

echo "==================== 2) TRANSACCIÓN CON FALLO Y COMPENSACIÓN (proveedor PRV-SIN-CUPO)"
KO=$(crear TRB-KO-$RANDOM PRV-SIN-CUPO); sleep 1.5
R=$(curl -s -X POST "$BFF/bff/cotizaciones/$KO/aceptar"); S_KO=$(echo "$R" | "$PY" -c 'import sys,json;print(json.load(sys.stdin)["id_saga"])')
echo "   POST /bff/cotizaciones/$KO/aceptar -> 202, id_saga=$S_KO"
esperar_saga "$S_KO" COMPENSADA && echo "   saga COMPENSADA" || echo "   (timeout esperando COMPENSADA)"
estado "$KO"; mostrar_log "$S_KO"
echo "   historia event-sourced de la cotización (la compensación es un evento más, no un borrado):"
curl -s "$BFF/bff/cotizaciones/$KO/historia" | "$PY" -c 'import sys,json;h=json.load(sys.stdin);print("   ", [(e["seq"], e["tipo"]) for e in h["historia"]], "-> replay:", h["reconstruida_por_replay"]["estado"])'
echo

echo "==================== 3) RESUMEN (GET /bff/sagas)"
curl -s "$BFF/bff/sagas" | "$PY" -c 'import sys,json;print("   sagas por estado:", json.load(sys.stdin)["por_estado"])'
echo
echo "Consultas SQL sobre el SAGA LOG (cliente sqlite3), ver docs/SAGA.md; por ejemplo:"
echo "  docker compose exec saga sqlite3 -header -column /app/src/saga/api/saga.db \\"
echo "    \"SELECT secuencia, tipo, paso, servicio, mensaje FROM saga_log WHERE id_saga='$S_KO' ORDER BY secuencia;\""
