# Entrega 3 — Diseño y Experimentación
## Hogar de los Alpes · Equipo HdA · MISO 2026-14

**Repositorio público:** <https://github.com/JuanJoseRestrepo33/Event-drive-architecture-and-DD-project>
<!-- TODO: reemplazar por la URL real del repositorio del equipo -->

## Contenido
- `servicio-cotizaciones/` — implementación del servicio con DDD + eventos
  (README propio con el mapeo detallado a la rúbrica y cómo ejecutar).
- `docker-compose.yml` — infraestructura local: **PostgreSQL** (obligatorio) y
  Apache Pulsar (opcional, perfil `broker`).
- `servicio-cotizaciones/README.md` — guía paso a paso para levantar y probar todo.

## Cómo ejecutar (resumen)

```bash
docker compose up -d db                 # PostgreSQL
cd servicio-cotizaciones
python3.12 -m venv .venv && source .venv/bin/activate   # Windows: py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
PYTHONPATH=src python -m pytest tests/ -v               # Windows: $env:PYTHONPATH="src"
PYTHONPATH=src python src/cotizaciones/main.py          # API en http://localhost:5000
```

Detalle completo (endpoints, verificación en `psql`, broker opcional) en
`COMANDOS.md` y en `servicio-cotizaciones/README.md`.

## Mapeo con los criterios de revisión
| Criterio | Dónde |
|---|---|
| 3 escenarios del atributo 1 (Escalabilidad) | Láminas 2-4 (E1 pico 4x, E2 expansión global 3x/4-5x, E3 fan-out de eventos) |
| 3 escenarios del atributo 2 (Modificabilidad) | Láminas 5-7 (E4 despliegue independiente, E5 país nuevo sin tocar núcleo, E6 evolución de contrato v1→v2) |
| 3 escenarios del atributo 3 (Disponibilidad) | Láminas 8-10 (E7 caída de pasarela, E8 pérdida de AZ del broker, E9 partner ruidoso) |
| Implementación DDD + eventos | `servicio-cotizaciones/` (dominio 9 + hexagonal 9 + BD 9 + eventos entre módulos 9 + CQS 9; ver su README) |
| Template y indicaciones | Se llenó el template oficial sin alterar su estructura; cada escenario tiene fuente, estímulo, ambiente, artefacto, respuesta, medida, 3 decisiones con sensibilidad/tradeoff/riesgo, justificación y diagrama |

## Notas exigidas por el enunciado
- **Volúmenes**: las medidas igualan o superan el enunciado (E1: ~1.160 req/s ≥
  4x de 25M/día; E2: 36.000 trabajos/día y ≥1.450 req/s; E3: ~7,2M eventos/día).
- **Expansión global**: E2 (capacidad) y E5 (modificabilidad) la resuelven
  explícitamente: país nuevo = configuración + conectores, 0 cambios en el núcleo.
- **Medios de comunicación**: lámina 11 (dominio / integración thin / fat /
  comandos) y su materialización en el código (`schema/v1`, despachadores).
- **Persistencia**: PostgreSQL 16 vía `docker-compose`
