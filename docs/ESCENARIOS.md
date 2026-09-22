# Escenarios de calidad probados en la POC

La Entrega 2 priorizó tres atributos de calidad (escalabilidad, modificabilidad,
disponibilidad) y la Entrega 3 definió nueve escenarios, tres por atributo. Para la POC se
eligió **uno por atributo** con tres criterios: que fuera relevante para el negocio (no un
atributo "fácil de probar"), que fuera ejecutable a escala de POC, y que demostrara la
capacidad de la arquitectura para la **expansión global** (MX/BR/AR, 3x trabajos, 4-5x
integraciones).

| # | Atributo | Escenario (Entrega 3) | Estímulo original | Medida original |
|---|---|---|---|---|
| E1 | Escalabilidad | Pico climático 4x en 48 h | Granizada: partners suben de ~290 a ~1.160 req/s | 0 % rechazos; ACK p99 < 800 ms; la cola drena < 6 h |
| E6 | Modificabilidad | Evolución del contrato v1→v2 | Un productor publica una versión nueva de un evento con 8+ consumidores en producción | Downtime 0; consumidores rotos 0; convivencia v1/v2 ≥ 30 días |
| E7 | Disponibilidad | Caída de la pasarela de pagos 30 min | La pasarela responde 5xx en hora pico | Núcleo 100 %; 0 pagos perdidos; 0 duplicados; recuperación < 5 min |

Por qué estos tres y no otros: E1 es el escenario que origina toda la arquitectura reactiva
(el negocio no puede rechazar siniestros durante una granizada); E6 se prefirió sobre E4
(despliegue independiente) porque la rúbrica descarta pruebas del tipo "se agregó un método en
menos de un día", y la evolución de contratos con 30+ partners es la modificabilidad que importa;
E7 es el escenario crítico: protege la promesa "una fuga de agua no puede esperar", y es el mismo
tipo de experimento que sugiere la guía del curso (degradar un componente y seguir operando).

Cada escenario es un script en `escenarios/` que actúa como cliente (publica comandos y eventos
al broker y consulta por HTTP), verifica criterios con aserciones y termina en **CUMPLIDO** o
**FALLIDO**.

---

## Cómo ejecutarlos

### Modo A — Docker + Apache Pulsar
Los escenarios corren en un contenedor cliente (`escenarios/Dockerfile`) que comparte la red de
compose con el broker y los servicios (en Windows no hay `pulsar-client` para el host).
```bash
docker compose up --build -d
docker compose build escenarios
docker compose run --rm escenarios python escenario_e1_escalabilidad.py      # -e N=2000 para más carga
docker compose run --rm escenarios python escenario_e6_modificabilidad.py
bash escenarios/e7_docker.sh
```
`e7_docker.sh` ejecuta E7 **por fases** porque un contenedor no puede parar a otro: el host hace
`docker compose stop pagos` → `--fase caida` en el contenedor → `docker compose start pagos` →
`--fase recuperacion`. El estado entre fases (ids, eventos capturados) se guarda en
`escenarios/estado/e7.json`.

### Modo B — sin Docker (adaptador de archivos)
```bash
bash escenarios/validar_todo.sh          # levanta 4 servicios + BFF, corre E1+E6+E7, apaga todo
```
Los logs de cada servicio quedan en `/tmp/hda_logs/` y el del pagos relanzado por E7 en
`/tmp/pagos_respawn.log`.

### Traza única (demo)
`traza_unica.py` sigue **un solo hecho** por los cuatro servicios y termina mostrando el event
store; ideal con `docker compose logs -f` en otra terminal:
```bash
docker compose run --rm escenarios python traza_unica.py       # -e PAIS=MX -e MONEDA=MXN
```

---

## E1 — Escalabilidad: pico de creación masiva

**Diseño.** Se publica una ráfaga de `N` comandos `CrearCotizacion` al tópico
`comandos-cotizacion` (por defecto 60; `N=1000` en el documento de resultados). Un observador suscrito a
`eventos-cotizacion` inicia la **transacción larga** por cada cotización creada (publica
`IniciarSagaAceptacion` a `comandos-saga`); el orquestador conduce aceptar → retener → agendar.
Se espera a que pagos alcance exactamente `N` reservas.

**Qué se mide / criterios.**
- Publicación: 0 rechazos (el broker encola) y throughput.
- Drenaje end-to-end hasta pagos: reservas == N **exactas** (ni faltantes ni duplicados).
- Tiempo de drenaje.

**Salida real (modo B, N=30):**
```
== E1: ráfaga de 30 comandos CrearCotizacion (pico 4x a escala POC) ==
   publicados 30 en 0.00s (52,298 comandos/s) — 0 rechazos (el broker encola)
   drenaje end-to-end: 30 reservas en 1.0s · notificaciones acumuladas: 90
== E1 CUMPLIDO: 0 rechazos, drenaje completo, reservas exactas 30/30 (idempotencia) ==
```

**Qué demuestra.** No que "Pulsar encola", sino el patrón completo con el que el negocio absorbe
la granizada: buffering en el broker → consumidores que drenan a su ritmo → idempotencia que
garantiza conteos exactos. Las tácticas de la Entrega 3 (autoescalado por lag, particiones por
trabajo) se apoyan en este comportamiento base.

---

## E6 — Modificabilidad: evolución del contrato v1 → v2 sin romper consumidores

**Diseño.** El servicio de cotizaciones ya publica `CotizacionAceptada` **v2** (agrega el campo
`pais` para la expansión global). Notificaciones es un consumidor **escrito contra v1**. El
escenario publica al mismo tópico un evento v1 (sin `pais`) y uno v2 (`pais=AR`) y verifica que
notificaciones procesa ambos y registra la versión recibida.

**Criterios.** Consumidores rotos = 0; v1 y v2 conviven en el mismo tópico; downtime = 0.

**Salida real:**
```
== E6: publicando CotizacionAceptada v1 y v2 al mismo tópico ==
   v1 publicado (sin pais) · v2 publicado (pais=AR, expansión global)
   consumidor v1 procesó ambas: versiones nuevas registradas = ['v1', 'v2']
== E6 CUMPLIDO: consumidores rotos = 0, convivencia v1/v2 en el tópico, downtime = 0 ==
```
En el log de notificaciones: `CotizacionAceptada v2 recibida — campo pais ignorado (consumidor v1)`.

**Qué demuestra.** La política de versionamiento (JSON + `specversion` en el envelope +
evolución BACKWARD: una versión nueva solo agrega campos opcionales) funciona en ejecución.
Habilitar un país nuevo es dato + evolución compatible del contrato, no re-arquitectura — la tesis
de E2/E5 de la Entrega 3.

---

## E7 — Disponibilidad: caída de la pasarela de pagos (escenario crítico)

**Diseño.** Se detiene el servicio pagos (SIGTERM al proceso en modo B; `docker compose stop pagos`
en modo A) mientras se inician N transacciones largas (saga), y se verifican **cuatro mediciones**,
no una afirmación (más la quinta: todas las sagas terminan `COMPLETADAS` en el Saga Log):

1. **Disponibilidad del núcleo durante la caída.** 10 sondas HTTP a cotizaciones mientras pagos
   está muerto; además el núcleo crea y acepta N cotizaciones y publica sus eventos.
2. **RPO = 0.** Al rearrancar pagos, el broker le entrega los N eventos retenidos: reservas N/N,
   perdidos 0.
3. **RTO medido** desde el rearranque hasta el drenaje completo.
4. **Duplicados = 0 probado activamente.** Se re-inyectan 5 copias exactas de eventos ya
   procesados (la re-entrega *at-least-once* que hace un broker real tras un fallo) y pagos y
   trabajos las ignoran. La cadena se cierra: cada pago retenido termina en un trabajo agendado.

**Salida real (modo B, N=15):**
```
== E7 [1/4] deteniendo PAGOS (simula caída de la pasarela 30 min) ==
   pagos: caído (sin respuesta HTTP)
   con pagos caído: creando y aceptando 15 cotizaciones + 10 sondas al núcleo
   núcleo: 15/15 aceptadas y publicadas · disponibilidad 100% (10/10 sondas) · pagos sigue caído: True
   eventos retenidos en el broker esperando a pagos: 15
== E7 [2/4] rearrancando PAGOS — el broker debe entregar TODO lo retenido ==
   RTO = 0.5s hasta drenar · reservas 15/15 · perdidos = 0
== E7 [3/4] cierre del ciclo: PagoRetenido -> trabajo AGENDADO ==
   trabajos agendados 15/15 (cada pago retenido terminó en un trabajo)
== E7 [4/4] re-inyectando 5 eventos YA procesados (re-entrega at-least-once) ==
   tras la re-entrega: reservas 15/15, trabajos 15/15 -> duplicados en pagos = 0, en trabajos = 0
== E7 CUMPLIDO: núcleo 100% disponible durante la caída · perdidos = 0 (RPO=0) · RTO = 0.5s ·
   duplicados = 0 con 5 re-entregas inyectadas · cadena cerrada 15/15 ==
```
Evidencia en el log del pagos relanzado: 15 líneas `CONSUMIDO CotizacionAceptada` seguidas y
5 líneas `duplicado … IGNORADO (idempotencia)`.

**Qué demuestra.** Las tácticas de disponibilidad de la Entrega 3 implementadas y verificadas:
desacople por broker (pagos es consumidor, no dependencia síncrona del núcleo), retención y
re-entrega del broker, consumidores idempotentes (marca del mensaje en la misma transacción que
el efecto) y eventos autosuficientes (`PagoRetenido` lleva `id_trabajo` y `pais`, así trabajos no
consulta a nadie). En producción el RTO crece con el backlog; por eso la Entrega 3 fija < 5 min y
autoescalado por lag.

---

## Qué NO prueba la POC (y por qué)

- **E8 (pérdida de una zona del broker):** requiere un clúster Pulsar multi-broker con
  replicación; la POC usa Pulsar standalone. Queda diseñado en la Entrega 3 (factor 3, acks=all).
- **Latencias absolutas de producción:** los números (RTO 0,5 s, drenaje 1 s) son de la POC a
  escala reducida; lo que se valida es el comportamiento (0 rechazos, 0 perdidos, 0 duplicados),
  no la cifra.
- **Fallos del propio orquestador con timeouts:** la saga espera indefinidamente el evento de un
  participante caído (correcto para E7); un timeout que lleve la saga a `FALLIDA` con
  intervención manual queda como trabajo futuro (ver `docs/REFINAMIENTO-ARQUITECTURA.md` §8).
