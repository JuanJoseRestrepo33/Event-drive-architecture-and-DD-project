#!/usr/bin/env python3
"""ESCENARIO E6 (Modificabilidad — Entrega 3): evolución de esquema
v1 -> v2 sin romper consumidores.

El productor (cotizaciones) YA publica CotizacionAceptada v2 (campo nuevo
'pais', para la expansión global). Notificaciones es un consumidor escrito
contra v1. Este escenario publica un v2 manualmente y verifica:
  1. El consumidor v1 lo procesa SIN romperse (ignora 'pais').
  2. v1 y v2 conviven en el mismo tópico (BACKWARD).
"""
import uuid

from comun import broker_mod, contratos, get, esperar, NOTIFICACIONES

bk = broker_mod.broker()

print("== E6: publicando CotizacionAceptada v1 y v2 al mismo tópico ==")
idc = str(uuid.uuid4())
v1 = contratos.evento_cotizacion_aceptada_v1(idc, "TRB-E6", "PRV-1", 50000, "COP")
bk.publicar("eventos-cotizacion", v1)
idc2 = str(uuid.uuid4())
v2 = contratos.evento_cotizacion_aceptada_v2(idc2, "TRB-E6", "PRV-1", 80000, "ARS", pais="AR")
bk.publicar("eventos-cotizacion", v2)
print("   v1 publicado (sin pais) · v2 publicado (pais=AR, expansión global)")

def _mias():
    """Notificaciones generadas por LOS DOS eventos de este escenario
    (el mensaje incluye el prefijo del id de cotización)."""
    return [n for n in get(NOTIFICACIONES + "/notificaciones")
            if n["tipo"] == "CotizacionAceptada"
            and (idc[:8] in n["mensaje"] or idc2[:8] in n["mensaje"])]

esperar(lambda: len(_mias()) >= 2, timeout=30, descripcion="2 notificaciones de este escenario")
versiones = {n["version"] for n in _mias()}
print(f"   consumidor v1 procesó ambas: versiones nuevas registradas = {sorted(versiones)}")
ok = {"v1", "v2"} <= versiones
print(f"== E6 {'CUMPLIDO' if ok else 'FALLIDO'}: consumidores rotos = 0, "
      f"convivencia v1/v2 en el tópico, downtime = 0 ==")
raise SystemExit(0 if ok else 1)
