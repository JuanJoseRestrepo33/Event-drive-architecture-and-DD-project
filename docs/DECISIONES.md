# Decisiones de arquitectura

Registro de las decisiones de diseño de la POC, con su justificación y los tradeoffs asumidos.
Cada una se puede verificar en el código; se indica dónde.

## 1. Comunicación: solo comandos y eventos sobre Apache Pulsar

**Decisión.** Toda la comunicación entre servicios es asíncrona por Pulsar. Cada servicio tiene
**su propio tópico de comandos** (`comandos-cotizacion`, `comandos-pago`, `comandos-trabajo`,
`comandos-notificacion`) y publica hechos a **su tópico de eventos** (`eventos-cotizacion`,
`eventos-pago`, `eventos-trabajo`). No existe ningún llamado HTTP ni gRPC entre servicios; los
endpoints GET son queries para clientes (a través del BFF) y para los escenarios.

**Por qué.** Es lo que hace reales el desacople y la resiliencia que la Entrega 3 promete: un
servicio caído no bloquea a los demás (E7), el broker absorbe picos (E1) y cada servicio evoluciona
solo (E6). Un llamado síncrono reintroduce acoplamiento temporal: si pagos llamara a cotizaciones
por HTTP, la caída de uno sería la caída de los dos.

**Cómo.** Al consumir un evento de integración, cada servicio lo traduce a *su* comando de
aplicación y lo ejecuta por el mismo camino (`ejecutar_commando`) que un comando recibido
directamente por su tópico. Esa simetría es la base de la saga orquestada de la Entrega 5: el
orquestador solo tendrá que publicar los comandos que ya existen.

**Uso de Pulsar** (`seedwork/infraestructura/broker.py`): un cliente por proceso con un productor
por tópico; suscripciones `Shared` (varios consumidores de una suscripción reparten carga);
`acknowledge` **después** de aplicar el efecto y `negative_acknowledge` ante error (reintento);
`initial_position=Earliest` (una suscripción nueva no pierde lo publicado antes de crearse).

**Tradeoff.** Consistencia eventual y más complejidad operativa (tópicos, suscripciones,
idempotencia) — exactamente los sacrificios que el árbol de utilidad de la Entrega 2 declaró
aceptables a cambio de escalabilidad, modificabilidad y disponibilidad.

## 2. Topología de datos: descentralizada

**Decisión.** *Database per service*: cada microservicio es dueño exclusivo de su base de datos
(`cotizaciones.db`, `pagos.db`, `trabajos.db`, `notificaciones.db`); ningún servicio lee ni
escribe la base de otro. Lo único compartido es el contrato de mensajes.

**Por qué.** (a) Autonomía de despliegue y de evolución del esquema por equipo — el dolor del
monolito de la Entrega 1 era un esquema compartido que obligaba a coordinar a todos (meta: pasar
de 50 a 100 ingenieros). (b) Escalado y tuning independientes (E1). (c) Aislamiento de fallas: la
caída de pagos no toca los datos de cotizaciones (E7). (d) Modelos distintos por contexto:
cotizaciones necesita Event Sourcing; pagos y trabajos, CRUD con unicidad.

**Por qué no híbrida.** Ningún par de servicios de este flujo comparte invariantes
transaccionales que justifiquen una base común; agrupar pagos y trabajos reintroduciría el
acoplamiento de esquema que se quiere eliminar.

**Tradeoff.** Sin joins entre servicios: la composición se hace por eventos (cada consumidor
recibe en el mensaje lo que necesita) o por el BFF (que compone queries); consistencia eventual;
cuatro bases que operar y migrar. `DB_URL` permite cambiar SQLite por PostgreSQL sin tocar código.

## 3. Modelo de datos por servicio: Event Sourcing y CRUD

| Servicio | Modelo | Por qué |
|---|---|---|
| Cotizaciones | **Event Sourcing** + proyección | Dinero en juego: auditoría natural de cada cambio; replay para proyecciones nuevas; el comando `AceptarCotizacion` reconstruye el agregado desde su historia (`reconstruir` → `desde_historia`). La proyección `cotizaciones` (read model) se actualiza en la **misma Unidad de Trabajo** que el *append* al store, y la sirven las queries. |
| Pagos | **CRUD idempotente** | El escrow es estado simple con unicidad por cotización; lo crítico es la idempotencia ante re-entregas (E7). |
| Trabajos | **CRUD idempotente** | Agenda confirmada; regla: no se agenda sin pago retenido. |
| Notificaciones | **CRUD idempotente** | Registro de salida; no requiere historia reconstruible. |

**Proyecciones y consultas con ES.** `GET /cotizaciones/{id}` lee la proyección (rápida);
`GET /cotizaciones/{id}/historia` devuelve el event store y el agregado reconstruido por replay,
demostrando que el estado es función de sus eventos.

**Idempotencia como parte del modelo.** Puerto `RepositorioEventosProcesados`; el handler del
comando registra en la misma Unidad de Trabajo el efecto de negocio y la marca del mensaje
consumido. Una re-entrega (`at-least-once`) se detecta y se ignora (E7 lo prueba activamente).

## 4. Eventos: tipo, formato y versionamiento

**Tipo: eventos de integración *thin*** (llaves y datos esenciales para decidir), separados de los
**eventos de dominio** (internos, con tipos de Python; en cotizaciones son los registros del
store). Se descartó *carga de estado* (fat) porque acoplaría el esquema completo del agregado a
todos los consumidores, los consumidores de este flujo deciden con pocos datos, y el volumen de
la Entrega 3 (~7,2 M eventos/día con fan-out) lo penaliza. Dónde sí usaríamos carga de estado:
read models de la consola de agentes (E3, Entrega 3), donde el consumidor solo proyecta una vista.

**Punto medio consciente.** `PagoRetenido` lleva `id_trabajo` y `pais` aunque pagos no los use:
son lo que trabajos necesita para no tener que consultar a nadie. El productor incluye lo que la
cadena necesita para no preguntar, y nada más.

**Formato: JSON.** Legible en logs, tópicos y depuración (lo que en una POC de arquitectura vale
más que el ahorro de bytes); sin toolchain de compilación ni dependencias nativas; formato
natural del cliente Pulsar en Python. *Tradeoff:* sin validación automática de esquema en el
broker (que daría Avro + Schema Registry); lo mitiga que los esquemas viven en un solo lugar por
servicio (`schema/v1`, `schema/v2`). Migrar a Avro es un adaptador más, no un cambio de
arquitectura.

**Versionamiento: propio, en el envelope.** Cada mensaje lleva `specversion` (`v1`, `v2`) junto a
`id`, `time`, `type`, `class` (comando|evento) y `service_source`. Versionar por mensaje y no por
nombre de tópico permite que **v1 y v2 convivan en el mismo tópico** y que cada consumidor migre
a su ritmo (E6). **Política BACKWARD:** una versión nueva solo agrega campos opcionales (v2 de
`CotizacionAceptada` añade `pais`), nunca renombra ni elimina; un consumidor v1 procesa v2
ignorando lo nuevo. Un cambio incompatible exige un tipo de evento nuevo.

## 5. Saga orquestada con Saga Log

**Decisión.** La transacción larga *aceptar cotización* (cotizaciones → pagos → trabajos) se
coordina por **orquestación**: un servicio `saga` con agregado `Saga`, base propia y **Saga Log**
append-only. Los participantes consumen solo comandos de su tópico y responden con eventos; las
compensaciones (`RevertirPago`, `RevertirAceptacion`) son acciones de negocio en orden inverso.

**Por qué orquestación y no coreografía.** (1) Visibilidad: con 30+ partners y SLAs, soporte debe
responder "¿en qué paso está y por qué falló?" en una consulta; el estado vive en un solo lugar.
(2) Las compensaciones tienen orden y dependencias (liberar escrow antes de revertir la
aceptación). (3) Evolucionar la transacción (p. ej. *verificar cobertura* para MX/BR/AR) es una
entrada más en la definición de pasos. (4) Sin "dios": el orquestador no valida reglas de dominio,
solo secuencia; las reglas siguen en cada agregado. Notificaciones sigue en coreografía porque no
participa en la transacción. Justificación completa, modelo y SQL en `docs/SAGA.md`.

**Tradeoff.** Un componente más (se mitiga con idempotencia y estado en base: si cae, reanuda), y
un punto donde una caída pausa las transacciones nuevas sin perderlas (los mensajes esperan en
Pulsar).

## 6. BFF como única puerta síncrona

**Decisión.** Un servicio `bff` (puerto 5000) expone REST a clientes. Los `POST` publican comandos
a los tópicos y responden `202 Accepted`; los `GET` son queries síncronas que el BFF compone (p.
ej. `GET /bff/cotizaciones/{id}/estado` reúne cotización, pago, trabajo y notificaciones). No tiene
base de datos ni reglas de negocio.

**Por qué.** Los clientes (app móvil, partners, Postman) necesitan un contrato HTTP estable y
simple; internamente el sistema es asíncrono. El BFF traduce entre ambos mundos y evita que el
cliente conozca cuatro servicios y cuatro tópicos. Al no tener lógica, no compite con el dominio:
un comando puede ser rechazado por una regla aunque el BFF haya respondido 202.

**Detalle.** El BFF genera el `id` de la cotización y lo envía en el comando; cotizaciones lo
respeta (identidad decidida por el cliente). Así el cliente puede consultar el recurso con el id
del 202 sin necesidad de un canal de respuesta.

## 7. DDD

Los cuatro microservicios comparten la anatomía del tutorial 7 (`src/<servicio>/seedwork`,
`config`, `modulos/<bc>/{dominio, aplicacion, infraestructura}`, `api`, `main.py`).

- **Contextos acotados** = servicios (Cotizaciones, Pagos, Gestión de Trabajos, Notificaciones),
  cada uno con su lenguaje, su modelo, su base de datos y su tópico de comandos. Relación entre
  contextos: Published Language (eventos de integración versionados); los esquemas actúan como
  Shared Kernel copiado y versionado en cada servicio.
- **Agregaciones** (raíces con `AgregacionRaiz`): `Cotizacion` (event-sourced: `aplicar`,
  `desde_historia`), `ReservaDePago`, `AgendaDeTrabajo`, `Notificacion` y `Saga` (cuyo evento de
  dominio `EntradaSagaLog` se persiste como fila del Saga Log). Cada una con su **fábrica** que
  valida reglas al construir.
- **Objetos valor**: `Dinero(monto, Moneda)` (COP/MXN/BRL/ARS, expansión global), estados como
  enums; `dataclass(frozen=True)`, sin identidad.
- **Reglas de negocio** explícitas: `MontoDebeSerPositivo`, `SoloEmitidaSePuedeAceptar`,
  `DebeExistirPagoRetenido`, `DestinatarioObligatorio`.
- **Capas / arquitectura cebolla**: `dominio/` no importa Flask, SQLAlchemy ni el broker;
  `aplicacion/` orquesta (comandos, queries, DTOs, Unidad de Trabajo); `infraestructura/`
  implementa los puertos (repositorios SQLAlchemy, mapeadores, despachadores, consumidores).
- **Inversión de dependencias**: `RepositorioCotizaciones`, `RepositorioEventosCotizaciones`,
  `RepositorioEventosProcesados` son interfaces del dominio; `FabricaRepositorio` entrega la
  implementación. El broker es un puerto del seedwork con adaptadores Pulsar/archivo elegidos por
  variable de entorno.
- **Unidad de Trabajo** (tutorial 7): `registrar_batch` + `commit`; señal `<Evento>Dominio`
  pre-commit (escribe el event store en cotizaciones) y `<Evento>Integracion` post-commit →
  despachador → tópico. Un solo commit contiene el efecto y la marca de idempotencia.
- **Consumidores y UoW**: cada mensaje del broker se ejecuta en un `test_request_context()` de
  Flask para que la Unidad de Trabajo del tutorial (guardada en sesión) funcione fuera del ciclo
  HTTP sin modificar el seedwork.

## 8. Despliegue

**Decisión.** Un contenedor Docker por microservicio + BFF + Apache Pulsar, orquestados con Docker
Compose; idéntico en Docker Desktop (desarrollo) y en una VM Linux de Google Cloud Compute Engine
(`README-GCP.md`).

**Por qué.** Un contenedor por servicio es la unidad de despliegue independiente que exige E4 de
la Entrega 3; la imagen validada localmente es la que se despliega; resuelve la falta de
`pulsar-client` para Windows; una VM basta para la POC (no se justifica Kubernetes aún); las
mismas imágenes pasan a GKE y Pulsar standalone a un clúster administrado cuando la expansión
global lo exija, cambiando solo `BROKER_HOST`.

## 9. Adaptador de archivos para desarrollo

**Decisión.** El puerto del broker tiene un segundo adaptador (`ArchivoBroker`: un `.jsonl` por
tópico y un offset por suscripción) para correr y probar la POC multi-proceso sin Docker.

**Por qué.** Desarrollo y pruebas rápidas en cualquier máquina; demuestra la inversión de
dependencias (cambiar de broker no toca dominio ni aplicación). **Lección aprendida:** un
adaptador de desarrollo puede ocultar semánticas del broker real — en Pulsar una suscripción nueva
arranca en `Latest` y el escenario E1 se colgaba hasta configurar `Earliest`. Por eso la
validación final siempre se hace contra Pulsar.
