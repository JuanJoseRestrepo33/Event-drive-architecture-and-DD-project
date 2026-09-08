# Servicio Cotizaciones de Hogar de los Alpes
## Entrega 3 · DDD + arquitectura basada en eventos (alineado al tutorial 5 del curso)

Servicio del contexto acotado **Cotizaciones**, implementado siguiendo el
seedwork y las convenciones de los tutoriales del curso (estructura de
`aeroalpes`, CQS + Unidad de Trabajo + eventos de dominio).

---

## Requisitos

- **Python 3.12** (la versión del curso).
- **Docker Desktop**, para levantar PostgreSQL.

## Cómo ejecutar

### 1. Levantar la base de datos (PostgreSQL)

```bash
docker compose up -d db
docker compose ps          # esperar a que 'hda-postgres' esté healthy
```

### 2. Crear el entorno e instalar dependencias

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Correr las pruebas y el servicio

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="src"
python -m pytest tests/ -v
python src/cotizaciones/main.py
```

**Linux / macOS:**
```bash
PYTHONPATH=src python -m pytest tests/ -v
PYTHONPATH=src python src/cotizaciones/main.py
```

### 4. Probar los endpoints

```bash
# Comando: crear cotización (lado C de CQS) -> 202 Accepted
curl -X POST http://localhost:5000/cotizaciones \
  -H "Content-Type: application/json" \
  -d '{"id_trabajo":"TRB-001","id_proveedor":"PRV-9","monto":250000,
       "moneda":"COP","categoria":"plomeria","descripcion":"cambio de tuberia",
       "vigencia_desde":"2026-01-01T00:00:00","vigencia_hasta":"2030-01-01T00:00:00"}'

# Query: consultar por id (lado Q de CQS)
curl http://localhost:5000/cotizaciones/<ID>

# Query: cotizaciones de un trabajo
curl "http://localhost:5000/cotizaciones?trabajo=TRB-001"

# Comando: aceptar (dispara el evento de dominio que consume el módulo pagos)
curl -X POST http://localhost:5000/cotizaciones/<ID>/aceptar
```

Para inspeccionar la BD y comprobar la persistencia real:

```bash
docker exec -it hda-postgres psql -U hda -d cotizaciones -c "\dt"
docker exec -it hda-postgres psql -U hda -d cotizaciones \
  -c "select id_cotizacion, estado, monto from reservas_pago;"
```

### 5. Broker de eventos — Apache Pulsar (OPCIONAL)

La comunicación **entre módulos** usa eventos de dominio en proceso y no
requiere broker. El broker solo se necesita para ver los eventos de
**integración** saliendo a un tópico real (Apache Pulsar, como en el
tutorial 5). Sin él, el despachador degrada a un log JSON-lines
(`eventos_integracion.log`) que simula el tópico: el puerto y el mapeo
dominio→integración no cambian (hexagonal).

> Requiere ~3-4 GB de RAM libres: el cluster son cuatro contenedores
> (zookeeper, pulsar-init, bookie, broker).

**a. Levantar el cluster**

```bash
docker compose --profile broker up -d
docker compose ps          # esperar 1-2 min a que 'hda-broker' esté arriba
```

**b. Instalar el cliente y apuntar el servicio al broker**

```bash
pip install pulsar-client
```

```powershell
# Windows (PowerShell)
$env:BROKER_HOST="localhost"
$env:PYTHONPATH="src"
python src/cotizaciones/main.py
```

```bash
# Linux / macOS / Git Bash
export BROKER_HOST=localhost
PYTHONPATH=src python src/cotizaciones/main.py
```

**c. Consumir el tópico para ver los eventos llegar**

En otra terminal, dejar el consumidor escuchando y luego ejecutar los
comandos del paso 4:

```bash
docker exec -it hda-broker bin/pulsar-client consume \
  persistent://public/default/eventos-cotizacion -s prueba -n 0
```

Al crear y aceptar una cotización deben aparecer los mensajes con
`type: CotizacionCreada` y `type: CotizacionAceptada`.

**d. Inspeccionar tópico y esquema (REST admin de Pulsar)**

```bash
# estadísticas del tópico (mensajes publicados, consumidores)
curl http://localhost:8080/admin/v2/persistent/public/default/eventos-cotizacion/stats

# esquema registrado (schema registry)
curl http://localhost:8080/admin/v2/schemas/public/default/eventos-cotizacion/schema
```

**Señal de que funcionó:** el archivo `eventos_integracion.log` deja de
crecer, porque el despachador ya no cae en el fallback — está publicando
al tópico real.

**e. Apagar**

```bash
docker compose --profile broker down     # conserva los datos
docker compose down -v                   # borra también los volúmenes
```

> Nota de configuración: la URL de la BD se resuelve con la variable de
> entorno `DB_URL` (por defecto la del `docker-compose`). No hay credenciales
> de producción ni datos sensibles en el repositorio.

---

## Mapeo

1. **Patrón dominio** — seedwork completo; agregado `Cotizacion`
   (raíz) + entidad interna `SolicitudDeVisita`; objetos valor `Dinero`
   (multi-moneda COP/MXN/BRL/ARS), `Alcance`, `Vigencia`; reglas
   (`MontoDebeSerPositivo`, `VigenciaDebeSerValida`,
   `SoloEmitidaSePuedeAceptar`, `NoSePuedeAceptarVencida`); fábricas
   `FabricaCotizaciones`/`_FabricaCotizacion` (validan reglas al crear);
   repositorios como puertos del dominio; módulos `cotizaciones` y `pagos`.
2. **Hexagonal** — puertos en `dominio/repositorios.py` y UoW;
   adaptadores: API Flask (entrada), SQLAlchemy/PostgreSQL (persistencia),
   despachador Pulsar/log (salida). El dominio no importa infraestructura.
3. **Manejador de BD** — **PostgreSQL 16** vía Flask-SQLAlchemy
   (`docker compose up -d db`); persistencia y consulta reales (ver tests y
   los comandos `psql` de arriba). No se usan bases de datos de prueba.
4. **Comunicación entre módulos por eventos de dominio** — la UoW
   emite la señal `CotizacionAceptadaDominio`; el módulo **pagos** está
   conectado a ella (`modulos/pagos/aplicacion/__init__.py`) y retiene el
   escrow (`ReservaPago`) en la misma transacción. Cotizaciones no conoce
   a pagos. Además, post-commit la señal `*Integracion` publica el evento
   de integración v1 (formato CloudEvents) al tópico `eventos-cotizacion`.
5. **CQS** — comandos `CrearCotizacion`/`AceptarCotizacion`
   (`ejecutar_commando`) y queries `ObtenerCotizacion`/
   `CotizacionesPorTrabajo` (`ejecutar_query`), con handlers separados;
   el API solo traduce.

**Plus:** event sourcing — cada evento del agregado queda en el event store
`eventos_cotizacion` (id_entidad, versión, tipo, payload JSON), poblado por
la UoW vía `repositorio_eventos_func`.
