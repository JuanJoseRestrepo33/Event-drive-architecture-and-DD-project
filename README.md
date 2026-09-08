# Entrega 3 - Diseño y Experimentación
## Hogar de los Alpes · Equipo 16 · MISO 2026-14

## Contenido
- [`servicio-cotizaciones/`](servicio-cotizaciones/) — implementación del servicio con DDD + eventos
  (README propio con el mapeo detallado a la rúbrica y cómo ejecutar).
- [`docker-compose.yml`](docker-compose.yml) — infraestructura local: **PostgreSQL** (obligatorio) y
  Apache Pulsar (opcional, perfil `broker`).
- [`servicio-cotizaciones/README.md`](servicio-cotizaciones/README.md) — guía paso a paso para levantar y probar todo.

## Cómo ejecutar (resumen)

> **Importante:** a partir de `cd servicio-cotizaciones`, todos los comandos
> siguientes deben ejecutarse dentro de esa carpeta.

```bash
# Opción A: parado en la raíz del repo (donde está docker-compose.yml)
docker compose up -d db                 # PostgreSQL

# Opción B: si ya estás dentro de servicio-cotizaciones/
docker compose -f ../docker-compose.yml up -d db

cd servicio-cotizaciones
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
PYTHONPATH=src python -m pytest tests/ -v               # Windows: $env:PYTHONPATH="src"
PYTHONPATH=src python src/cotizaciones/main.py          # API en http://localhost:5000
```

Detalle completo (endpoints, verificación en `psql`, broker opcional) en
[`servicio-cotizaciones/README.md`](servicio-cotizaciones/README.md).

## Mapeo con los criterios
| Criterio | Dónde |
|---|---|
| 3 escenarios del atributo 1 (Escalabilidad) | Láminas 2-4 (E1 pico 4x, E2 expansión global 3x/4-5x, E3 fan-out de eventos) |
| 3 escenarios del atributo 2 (Modificabilidad) | Láminas 5-7 (E4 despliegue independiente, E5 país nuevo sin tocar núcleo, E6 evolución de contrato v1→v2) |
| 3 escenarios del atributo 3 (Disponibilidad) | Láminas 8-10 (E7 caída de pasarela, E8 pérdida de AZ del broker, E9 partner ruidoso) |
| Implementación DDD + eventos | [`servicio-cotizaciones/`](servicio-cotizaciones/) (dominio 9 + hexagonal 9 + BD 9 + eventos entre módulos 9 + CQS 9; ver [su README](servicio-cotizaciones/README.md)) |
| Template y indicaciones | Se llenó el template oficial sin alterar su estructura; cada escenario tiene fuente, estímulo, ambiente, artefacto, respuesta, medida, 3 decisiones con sensibilidad/tradeoff/riesgo, justificación y diagrama |

