# Entrega 4 - Prueba de Concepto (POC)
## Hogar de los Alpes · Arquitectura de microservicios basada en eventos
## Equipo HdA

| Integrante | Código | Actividades |
|---|---|---|
| Sergio Fernando Barrera Molano | 202517034 | Servicio cotizaciones (event sourcing), servicio trabajos, escenario E1, docker-compose |
| Harold Andres Bartolo Moscoso | 202513889 | Servicio pagos (idempotencia), escenario E7, pruebas |
| Juan Jose Restrepo Bonilla | 202516633 | Servicio notificaciones, contratos v1/v2, escenario E6, README |

POC de 4 microservicios comunicados por **comandos y eventos vía Apache
Pulsar**, con topología de datos **descentralizada**, Event Sourcing + CRUD,
y la validación ejecutable de **3 escenarios de calidad de la Entrega 3**
(uno por atributo), probando la capacidad de la arquitectura para la
**expansión global** del negocio.

## Estructura del repositorio
```
entrega4-hogar-de-los-alpes/
├── docker-compose.yml          # Pulsar + 4 servicios
├── servicios/
│   ├── cotizaciones/           # Event Sourcing + proyección · comandos-cotizacion · eventos-cotizacion
│   ├── pagos/                  # CRUD idempotente · comandos-pago · eventos-pago
│   ├── notificaciones/         # CRUD idempotente · comandos-notificacion · consume 3 tópicos
│   └── trabajos/               # CRUD idempotente · comandos-trabajo · eventos-trabajo
│   (cada uno: Dockerfile, requirements.txt, src/<servicio>/{seedwork,config,modulos,api,main.py})
└── escenarios/
    ├── contratos.py                     # factorías de mensajes del cliente (BFF/partner simulado)
    ├── Dockerfile                       # contenedor cliente de escenarios (Modo A)
    ├── e7_docker.sh                     # E7 en Modo A: el host para/arranca pagos por fases
    ├── escenario_e1_escalabilidad.py
    ├── escenario_e6_modificabilidad.py
    ├── escenario_e7_disponibilidad.py   # crítico: sondas, RTO, cadena completa, re-entregas
    └── validar_todo.sh                  # runner integrado (modo B)
```

```
[escenarios/cliente] --COMANDOS--> (Pulsar: comandos-cotizacion)
                                          ↓
                 ┌──────────────────────────────────────┐
                 │ 1. COTIZACIONES (:5001)              │
                 │    EVENT SOURCING · BD propia        │──EVENTOS──> (eventos-cotizacion)
                 └──────────────────────────────────────┘                  ↓             ↓
                                              ┌──────────────────────┐            ┌───────────────────────────┐
                                              │ 2. PAGOS (:5002)     │            │ 3. NOTIFICACIONES (:5003) │
                                              │  CRUD idempotente    │─(eventos-pago)─>│  CRUD · consumidor v1     │
                                              │  BD propia           │      │     │  tolerante a v2 · BD propia│
                                              └──────────────────────┘      │     └───────────────────────────┘
                                                                            ↓                 ↑
                                              ┌──────────────────────┐      │                 │
                                              │ 4. TRABAJOS (:5004)  │<─────┘                 │
                                              │  CRUD idempotente    │─(eventos-trabajo)──────┘
                                              │  BD propia           │  (todo viaja en el evento)
                                              └──────────────────────┘
Los GET HTTP son SOLO para clientes/escenarios (queries síncronas permitidas). Entre
servicios NO existe ningún llamado HTTP/gRPC: solo comandos y eventos por Pulsar.
```

---

## Paso a paso de ejecución

### Modo A - Apache Pulsar con Docker (entrega oficial)

Requisito: Docker Desktop. Funciona igual en Windows (Git Bash), Mac y Linux:
**todo corre en contenedores**, incluidos los escenarios, porque `pulsar-client`
de Python no publica wheels para Windows.

```bash
# 1. Levantar el clúster Pulsar + los 4 microservicios
docker compose up --build -d
# (la primera vez tarda: descarga Pulsar ~560MB y espera su healthcheck)

# 2. Verificar salud
curl localhost:5001/health   # cotizaciones (event-sourcing)
curl localhost:5002/health   # pagos (crud)
curl localhost:5003/health   # notificaciones (crud)
curl localhost:5004/health   # trabajos (crud)

# 3. Construir el contenedor cliente de escenarios (una vez)
docker compose build escenarios

# 4. Correr los escenarios de calidad (cada uno en el contenedor cliente, conectado a Pulsar)
docker compose run --rm escenarios python escenario_e1_escalabilidad.py
docker compose run --rm escenarios python escenario_e6_modificabilidad.py
bash escenarios/e7_docker.sh      # E7: el host para/arranca pagos; el escenario corre en el contenedor
# opcional: más carga en E1 ->  docker compose run --rm -e N=2000 escenarios python escenario_e1_escalabilidad.py

# 5. Inspección manual (queries síncronas HTTP) y logs
curl localhost:5002/reservas                        # escrows retenidos
curl localhost:5003/notificaciones                  # notificaciones enviadas
curl localhost:5004/trabajos                        # trabajos agendados (cierre del ciclo)
curl "localhost:5001/cotizaciones/<id>"             # proyección (read model)
curl "localhost:5001/cotizaciones/<id>/historia"    # event store + agregado reconstruido por replay
docker compose logs -f pagos                        # trazas [uow] / [pagos] en vivo

# 6. Bajar todo
docker compose down -v
```

Cómo funciona E7 en Docker (`escenarios/e7_docker.sh`): `docker compose stop pagos`
→ `--fase caida` (sondas al núcleo, N aceptaciones, captura de eventos; guarda
estado en `escenarios/estado/e7.json`) → `docker compose start pagos` →
`--fase recuperacion` (RTO, RPO, cadena hasta trabajos, re-inyección de
duplicados). En Linux/Mac con `pip install pulsar-client` en el host también
sirve la versión de una sola pasada: `BROKER=pulsar BROKER_HOST=localhost
python escenarios/escenario_e7_disponibilidad.py --docker`.

### Modo B - Desarrollo sin Docker (broker de archivos)

El broker es un **puerto** con dos adaptadores (hexagonal): `pulsar` y
`archivo` (default). El modo B valida toda la lógica multi-proceso sin
infraestructura:

```bash
# Opción rápida (Linux/Mac/WSL): todo en un comando
bash escenarios/validar_todo.sh     # levanta los 4 servicios, corre E1+E6+E7, apaga todo

# Opción manual - Terminales 1 a 4 (una por servicio), desde la raíz del repo:
pip install -r servicios/cotizaciones/requirements.txt   # flask, flask-sqlalchemy, PyDispatcher
export BROKER=archivo BROKER_DIR=$PWD/broker_dev         # en Git Bash igual
cd servicios/cotizaciones   && PYTHONPATH=src python src/cotizaciones/main.py    # :5001
cd servicios/pagos          && PYTHONPATH=src python src/pagos/main.py           # :5002
cd servicios/notificaciones && PYTHONPATH=src python src/notificaciones/main.py  # :5003
cd servicios/trabajos       && PYTHONPATH=src python src/trabajos/main.py        # :5004

# Terminal 5: escenarios
cd escenarios
export BROKER=archivo BROKER_DIR=$PWD/../broker_dev
N=25 python escenario_e1_escalabilidad.py
python escenario_e6_modificabilidad.py
N_CAIDA=10 python escenario_e7_disponibilidad.py   # (modo dev: lee servicios/pagos/src/pagos/pagos.pid, que pagos escribe al arrancar)
```

Salida real de la validación integrada (`validar_todo.sh`, modo B):

```
== E1 CUMPLIDO: 0 rechazos, drenaje completo, reservas exactas 30/30 (idempotencia) ==
== E6 CUMPLIDO: consumidores rotos = 0, convivencia v1/v2 en el tópico, downtime = 0 ==
== E7 [1/4] deteniendo PAGOS (simula caída de la pasarela 30 min) ==
   pagos: caído (sin respuesta HTTP)
   núcleo: 15/15 aceptadas y publicadas · disponibilidad 100% (10/10 sondas) · pagos sigue caído: True
== E7 [2/4] rearrancando PAGOS - el broker debe entregar TODO lo retenido ==
   RTO = 0.5s hasta drenar · reservas 15/15 · perdidos = 0
== E7 [3/4] cierre del ciclo: PagoRetenido -> trabajo AGENDADO ==
   trabajos agendados 15/15
== E7 [4/4] re-inyectando 5 eventos YA procesados (re-entrega at-least-once) ==
   duplicados en pagos = 0, en trabajos = 0
== E7 CUMPLIDO: núcleo 100% disponible · perdidos = 0 (RPO=0) · RTO = 0.5s · duplicados = 0 con 5 re-entregas inyectadas · cadena cerrada 15/15 ==
```

Evidencia en logs (`/tmp/hda_logs/pagos.log` y `/tmp/pagos_respawn.log`): el pagos original
muere con la señal; el relanzado consume exactamente los 15 eventos retenidos y registra
5 líneas `duplicado ... IGNORADO (idempotencia)` para las re-entregas.

---

## Los 3 escenarios de calidad probados (coherentes con la Entrega 3)

| # | Atributo | Escenario (Entrega 3) | Qué prueba la POC | Criterio de éxito |
|---|---|---|---|---|
| E1 | **Escalabilidad** | Pico climático 4x en 48h | Ráfaga de N comandos al tópico; el broker absorbe (buffering) y el flujo drena end-to-end | 0 rechazos; reservas == N exactas; throughput medido |
| E6 | **Modificabilidad** | Evolución de contrato v1→v2 | El productor publica `CotizacionAceptada` **v2** (campo `pais`); notificaciones es un consumidor **v1** | Consumidores rotos = 0; v1 y v2 conviven en el tópico (BACKWARD) |
| E7 | **Disponibilidad** (crítico) | Caída de la pasarela 30 min | Se mata pagos; sondas al núcleo durante la caída; Pulsar retiene; al volver drena hasta **trabajos**; se **re-inyectan** eventos ya procesados | Núcleo 100% (sondas); perdidos = 0 (RPO=0); RTO medido; duplicados = 0 pese a re-entregas; cadena cerrada N/N |

### E7 en detalle - el escenario crítico
Es el escenario que protege la promesa del negocio ("una fuga de agua no
puede esperar"): el cobro es una dependencia externa frágil y NO puede
arrastrar al núcleo. La POC lo verifica con cuatro mediciones, no con una
afirmación:

1. **Disponibilidad del núcleo durante la caída** - sondas HTTP a
   cotizaciones mientras pagos está muerto: 10/10 = 100 %. Además el
   núcleo sigue creando/aceptando (15/15 eventos publicados al tópico).
2. **RPO = 0** - el broker retiene cada `CotizacionAceptada` hasta que un
   consumidor lo confirme (`acknowledge` en Pulsar / offset en el adaptador
   de archivo). Al volver pagos: reservas 15/15, perdidos = 0.
3. **RTO medido** - del rearranque al drenaje completo (0,5 s en la POC;
   en producción crece con el backlog, por eso el escenario de la Entrega 3
   fija < 5 min).
4. **Duplicados = 0 probado activamente** - se re-publican 5 copias exactas
   de eventos ya procesados (la re-entrega *at-least-once* que hace un
   broker tras un fallo) y pagos/trabajos los ignoran gracias a la tabla
   `eventos_procesados` escrita **en la misma transacción** que el efecto.

Tácticas implementadas: desacople por broker (pagos es consumidor, no
dependencia síncrona), consumidor idempotente, eventos autosuficientes
(`PagoRetenido` lleva `id_trabajo` y `pais`, así trabajos no consulta a
nadie) y cierre del ciclo hacia Trabajos para probar que la resiliencia
no es solo del primer salto.

**Expansión global** (nota del enunciado): el campo `pais` del comando y del
evento v2, el VO `Dinero` multi-moneda (COP/MXN/BRL/ARS) y el escenario E6
demuestran que habilitar un país nuevo es **dato + evolución compatible de
contrato**, no re-arquitectura - la misma tesis de E2/E5 de la Entrega 3.

---

## Mapeo con los criterios de revisión

### 1. Microservicios con comandos y eventos vía Apache Pulsar
- `docker-compose.yml` despliega un clúster Pulsar standalone y los **4 microservicios** (cotizaciones, pagos, notificaciones, trabajos).
- **Comandos**: cada servicio tiene su tópico de comandos - `comandos-cotizacion` (`CrearCotizacion`, `AceptarCotizacion`), `comandos-pago` (`RetenerPago`), `comandos-trabajo` (`AgendarTrabajo`), `comandos-notificacion` (`RegistrarNotificacion`) - intención dirigida, puede rechazarse por reglas. Es la base de la saga orquestada de la Entrega 5.
- **Eventos consumidos → comandos**: al consumir un evento de integración, cada servicio lo traduce a SU comando de aplicación y lo ejecuta con `ejecutar_commando` (mismo camino que un comando directo).
- **Eventos** (tópicos `eventos-cotizacion`, `eventos-pago`, `eventos-trabajo`): hechos publicados tras persistir.
- **Cero llamados síncronos entre servicios** (ni HTTP ni gRPC): cada consumidor recibe en el evento todo lo que necesita (p. ej. `PagoRetenido` ya lleva `id_trabajo` y `pais`). Los endpoints GET existen solo para clientes y para los escenarios de validación.
- Los servicios se oyen por tópicos **sin completar una transacción distribuida**: cada uno confirma su parte localmente y publica el hecho; la consistencia entre servicios es eventual.
- Suscripciones `Shared` con `negative_acknowledge` para reintentos (adaptador Pulsar en `broker.py`).

### 2. Topología de datos: DESCENTRALIZADA (definida, justificada, implementada)
Cada servicio es dueño exclusivo de su base de datos (`cotizaciones_es.db`,
`pagos.db`, `notificaciones.db`, `trabajos.db`) - nadie lee la BD de otro; solo se
comparte el **contrato de mensajes**. *Justificación*: (a) autonomía de
despliegue y evolución de esquema por equipo (el dolor del monolito de la
Entrega 1); (b) escalado y tuning independientes por servicio (E1);
(c) aislamiento de fallas: la caída de pagos no toca los datos de
cotizaciones (E7). *Tradeoff asumido*: no hay joins entre servicios (se
compone por eventos/queries) y la consistencia es eventual - exactamente
los sacrificios que el árbol de utilidad permitió (Entrega 2 §1.2).
*Por qué no híbrida*: ningún par de servicios de este flujo comparte
invariantes transaccionales que justifiquen BD común.

### 3. Modelo de datos por servicio (CRUD o Event Sourcing en los 4)
| Servicio | Modelo | Justificación |
|---|---|---|
| cotizaciones | **Event Sourcing** (tabla `eventos_cotizacion` append-only = fuente de verdad; el comando `AceptarCotizacion` **reconstruye** el agregado con `reconstruir` → `desde_historia`) + **proyección** `cotizaciones` (read model) actualizada en la misma UoW; queries: `GET /cotizaciones/<id>` lee la proyección, `GET .../historia` muestra el store y el replay | Auditoría natural del ciclo (dinero en juego), replay para proyecciones nuevas, y separación C/Q del tutorial 7 |
| pagos | **CRUD** + tabla de dedup en la misma transacción | El escrow es estado simple con unicidad por cotización; CRUD es suficiente y la idempotencia es lo crítico (E7/E8) |
| notificaciones | **CRUD** + dedup | Registro de salida; no requiere historia reconstruible |
| trabajos | **CRUD** idempotente | Agenda del trabajo confirmado (núcleo); estado simple con unicidad por cotización; regla: no se agenda sin pago retenido |

### 4. DDD en el diseño - estructura del tutorial 7 en los 4 servicios
Cada servicio es un paquete Python con la misma anatomía del tutorial del
curso (`src/<servicio>/`):

```
seedwork/                  # base reutilizable: Entidad, AgregacionRaiz, EventoDominio, ObjetoValor,
  dominio/ aplicacion/     #   ReglaNegocio + ValidarReglasMixin, Fabrica, Repositorio/Mapeador (puertos),
  infraestructura/         #   Comando/Query + ejecutar_commando/ejecutar_query (singledispatch),
  presentacion/            #   UnidadTrabajo + UnidadTrabajoPuerto (señales pydispatch), broker (puerto)
config/db.py, config/uow.py   # Flask-SQLAlchemy + UnidadTrabajoSQLAlchemy
modulos/<bc>/
  dominio/       entidades · objetos_valor · eventos · reglas · fabricas · repositorios (puertos) · excepciones
  aplicacion/    comandos/ · queries/ · dto · mapeadores · handlers (señales *Integracion)
  infraestructura/ dto (modelos SQLAlchemy) · repositorios · mapeadores · fabricas · despachadores ·
                   consumidores · schema/v1 (y v2) eventos de integración
api/           blueprint Flask (solo queries) · create_app
main.py
```

- **Contextos acotados** = servicios (Cotizaciones, Pagos, Notificaciones, Gestión de Trabajos), cada uno con su modelo, su BD y su tópico de comandos.
- **Agregaciones** (raíces con `AgregacionRaiz`): `Cotizacion` (event-sourced: `aplicar`/`desde_historia`), `ReservaDePago`, `AgendaDeTrabajo`, `Notificacion`; cada una con su fábrica que valida reglas al construir.
- **Objetos valor**: `Dinero` (+ enum `Moneda` multi-moneda) y los estados como enums; **reglas de negocio** como clases `ReglaNegocio` (`MontoDebeSerPositivo`, `SoloEmitidaSePuedeAceptar`, `DebeExistirPagoRetenido`, `DestinatarioObligatorio`).
- **Capas / arquitectura cebolla**: `dominio/` no importa Flask, SQLAlchemy ni el broker; `aplicacion/` orquesta con comandos, queries y la UoW; `infraestructura/` implementa los puertos (repositorios SQLAlchemy, despachadores, consumidores).
- **Inversión de dependencias**: repositorios y mapeadores son interfaces del dominio implementadas en infraestructura vía `FabricaRepositorio`; el broker es un puerto del seedwork con adaptadores Pulsar/archivo elegidos por configuración.
- **Unidad de Trabajo del tutorial**: `registrar_batch` + `commit`; las señales pydispatch `<Evento>Dominio` (pre-commit; escribe el event store en cotizaciones) y `<Evento>Integracion` (post-commit → despachador → tópico) son las mismas del tutorial 7.
- **Idempotencia como parte del modelo**: puerto `RepositorioEventosProcesados`; el handler del comando registra el efecto y la marca del mensaje en la misma UoW.
- **Shared Kernel**: los esquemas de integración (`schema/v1`, `schema/v2`) son la copia versionada del contrato en cada servicio; en producción, paquete gobernado por consenso (Entregas 2/3).

### 5. Tipos de eventos, formato y versionamiento de esquemas

**Tipo de evento - integración THIN** (ids + datos esenciales) y NO carga de
estado (fat): los consumidores de este flujo solo necesitan llaves, monto,
trabajo y país; un fat event acoplaría su esquema a todos los consumidores y
crecería sin control. Dónde SÍ usaríamos carga de estado: read models de la
consola de agentes (escenario E3 de la Entrega 3).

**Formato - JSON.** *Decisión*: el enunciado deja el formato a criterio del
equipo (Avro, protobuf, JSON…). Elegimos JSON porque (a) los mensajes son
legibles en logs, tópicos y depuración, lo que en una POC de arquitectura
vale más que el ahorro de bytes; (b) no requiere toolchain de compilación
de esquemas ni dependencias nativas en los 4 servicios; (c) es el formato
natural del adaptador de archivo y del cliente Pulsar en Python. *Tradeoff
asumido*: sin validación automática de esquema en el broker (que Avro +
Schema Registry sí daría) - lo compensamos con contract tests en CI y con
el módulo `contratos.py` como única fuente de los esquemas. Migrar a Avro
con Pulsar Schema Registry no cambia la arquitectura: es un adaptador más.

**Versionamiento - propio, en el envelope.** *Decisión*: cada mensaje lleva
`specversion` ("v1", "v2") junto a `type`, `id`, `time`, `class`
(comando|evento) y `service_source`. Elegimos versionado explícito por
mensaje, y no por nombre de tópico (`eventos-cotizacion-v2`), porque
permite que **v1 y v2 convivan en el mismo tópico** y que cada consumidor
migre a su ritmo (escenario E6). *Política de evolución*: **BACKWARD** -
una versión nueva solo AGREGA campos opcionales (v2 de `CotizacionAceptada`
añade `pais`), nunca renombra ni elimina; un consumidor escrito contra v1
procesa v2 ignorando lo nuevo. Un cambio incompatible exigiría un tipo de
evento nuevo, no una versión. Esquemas y política viven en `contratos.py`
(Shared Kernel copiado y versionado en cada servicio; en producción,
paquete gobernado por consenso - Entregas 2/3).

### 6. Despliegue: plataforma y justificación

*Decisión*: **contenedores Docker, uno por microservicio + uno para Apache
Pulsar, orquestados con Docker Compose**, ejecutados en una **VM Linux de
Google Cloud (Compute Engine, e2-standard-4, Ubuntu 22.04)**; la misma
composición corre idéntica en el portátil de cualquier miembro con Docker
Desktop. *Por qué*:

- **Un contenedor por servicio = la unidad de despliegue independiente** que
  exige la Entrega 3 (E4): cada imagen se construye, versiona y reinicia sola
  (`docker compose up --build pagos`), sin tocar a los demás.
- **Portabilidad**: la imagen que se valida localmente es la que se despliega;
  no hay "funciona en mi máquina".
- **Windows**: `pulsar-client` de Python no publica wheels para Windows;
  contenedores Linux eliminan el problema para todo el equipo.
- **Costo/tiempo de una POC**: una VM basta para 4 servicios + Pulsar
  standalone; no se justifica aún Kubernetes.
- **Camino de crecimiento sin rehacer nada**: las mismas imágenes pasan a
  GKE (Kubernetes) y Pulsar standalone se reemplaza por un clúster
  administrado cuando el volumen de la expansión global lo exija - los
  servicios no cambian, solo `BROKER_HOST`.

Pasos en la VM (una vez):
```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2
git clone <repo> && cd entrega4-hogar-de-los-alpes
sudo docker compose up --build -d
# abrir en el firewall de GCP los puertos 5001-5004 (y 8080 para Pulsar admin, opcional)
curl http://<IP_PUBLICA_VM>:5001/health
```
_Completar con la IP pública / captura del despliegue del equipo._

---