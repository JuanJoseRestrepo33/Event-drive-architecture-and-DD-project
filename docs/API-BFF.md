# API del BFF — Hogar de los Alpes

Base URL: `http://<host>:5000` (local: `http://localhost:5000`).

El BFF es la única puerta síncrona del sistema. Sus reglas:

- **`POST` = comando.** No ejecuta lógica: publica un COMANDO al tópico de Pulsar del servicio
  dueño y responde **`202 Accepted`**. El cuerpo del 202 incluye el `id` del recurso (generado por
  el BFF), el `id_comando`, el `topico` y `consultar_en` (dónde ver el resultado).
- **`GET` = query.** Consulta síncrona a uno o varios servicios; el BFF compone la respuesta.
- **Consistencia eventual.** Tras un `POST`, el `GET` puede tardar ~1-2 s en reflejar el cambio.
- **Un 202 no garantiza el efecto.** Un comando puede ser rechazado por una regla del dominio
  (p. ej. aceptar una cotización ya aceptada, monto negativo). El rechazo se ve en los logs del
  servicio (`RECHAZADO por regla`) y en que la proyección no cambia.

Envelope de todo comando publicado:
```json
{"id": "<uuid>", "time": 1758490000000, "specversion": "v1", "type": "CrearCotizacion",
 "class": "comando", "service_source": "bff", "data": { ... }}
```

---

## Salud y estadísticas

### `GET /bff/health`
Salud del BFF y de los 4 microservicios. `200` si todos están `up`; `503` si alguno cayó (útil para observar el escenario E7).
```json
{"bff":"up","cotizaciones":"up","pagos":"up","trabajos":"up","notificaciones":"up"}
```

### `GET /bff/stats`
Conteos por servicio: `eventos_en_store` (event sourcing), `reservas`, `trabajos_agendados`, `notificaciones`.

---

## Flujo principal (transacción larga)

### `POST /bff/cotizaciones` → comando `CrearCotizacion` (tópico `comandos-cotizacion`)
Cuerpo:
```json
{"id_trabajo": "TRB-001", "id_proveedor": "PRV-7", "monto": 220000, "moneda": "MXN", "pais": "MX"}
```
| Campo | Obligatorio | Notas |
|---|---|---|
| `id_trabajo` | sí | referencia al trabajo del contexto Gestión de Trabajos |
| `id_proveedor` | sí | |
| `monto` | sí | > 0 (regla `MontoDebeSerPositivo`; si no, el comando se rechaza) |
| `moneda` | sí | `COP` · `MXN` · `BRL` · `ARS` (objeto valor `Dinero`) |
| `pais` | no (default `CO`) | expansión global; viaja en el evento v2 |

Respuesta `202`:
```json
{"estado":"ACEPTADO","comando":"CrearCotizacion","id":"<id_cotizacion>","id_comando":"<uuid>",
 "topico":"comandos-cotizacion","consultar_en":"/bff/cotizaciones/<id_cotizacion>"}
```
`400` si faltan campos obligatorios.

El BFF genera el `id` de la cotización y lo envía en el comando; el servicio de cotizaciones lo
respeta (identidad decidida por el cliente), lo que permite consultar el recurso antes de que
exista sin necesidad de un canal de respuesta.

### `POST /bff/cotizaciones/{id}/aceptar` → comando `IniciarSagaAceptacion` (tópico `comandos-saga`)
Sin cuerpo. **Inicia la transacción larga** en el orquestador, que envía en orden `AceptarCotizacion`
→ `RetenerPago` → `AgendarTrabajo` esperando el evento de cada paso; si el trabajo se rechaza,
compensa (`RevertirPago` → `RevertirAceptacion`). Respuesta `202`:
```json
{"estado":"ACEPTADO","comando":"IniciarSagaAceptacion","id":"<id_cotizacion>","id_saga":"<id_saga>",
 "topico":"comandos-saga","consultar_en":"/bff/sagas/<id_saga>","estado_consolidado_en":"/bff/cotizaciones/<id>/estado"}
```
`404` si la cotización no existe aún. (`POST …/aceptar-sin-saga` publica `AceptarCotizacion` directo, solo para pruebas.)

### Sagas (monitoreo de transacciones largas)
| Endpoint | Devuelve |
|---|---|
| `GET /bff/sagas` | `{"por_estado": {...}, "sagas": [...]}` — conteo por estado y lista |
| `GET /bff/sagas/{id_saga o id_cotizacion}` | estado, `paso_actual`, `pasos_completados`, `motivo_fallo`, `datos`, fechas y **`log`** completo |
| `GET /bff/sagas/{ref}/log` | solo el Saga Log ordenado por `secuencia` |
| `GET /bff/sagas/log?n=50` | últimas N entradas de todas las sagas |

Entrada del Saga Log:
```json
{"secuencia": 11, "fecha": "…", "tipo": "COMPENSACION_ENVIADA", "paso": "RETENER_PAGO", "servicio": "pagos",
 "mensaje": "RevertirPago", "detalle": "Compensación RevertirPago → comandos-pago", "payload": "{…}"}
```
`estado` de una saga: `EN_CURSO` → `COMPLETADA`, o `COMPENSANDO` → `COMPENSADA` (o `FALLIDA`).

### `GET /bff/cotizaciones/{id}`
Proyección (read model) de la cotización. `404` si no existe (o el comando aún no se procesó).
```json
{"id":"…","id_trabajo":"TRB-001","id_proveedor":"PRV-7","monto":220000.0,"moneda":"MXN",
 "pais":"MX","estado":"ACEPTADA","version":2}
```

### `GET /bff/cotizaciones/{id}/estado`
**Vista consolidada de la transacción larga**, compuesta por el BFF a partir de los cuatro servicios:
```json
{"id_cotizacion":"…","fase":"TRABAJO_AGENDADO",
 "cotizacion": {"estado":"ACEPTADA","version":2, ...},
 "pago":       {"id":"…","estado":"RETENIDO","monto":220000.0,"moneda":"MXN","pais":"MX", ...},
 "trabajo":    {"id":"…","id_trabajo":"TRB-001","id_pago":"…","estado":"AGENDADO", ...},
 "notificaciones": [ {"tipo":"CotizacionAceptada","version":"v2", ...}, {"tipo":"TrabajoAgendado","version":"v1", ...} ]}
```
`fase` avanza: `EMITIDA` → `ACEPTADA` → `PAGO_RETENIDO` → `TRABAJO_AGENDADO`, o `COMPENSANDO` /
`COMPENSADA` si la saga falló. Incluye un resumen `saga` (`id_saga`, `estado`, `paso_actual`,
`pasos_completados`, `motivo_fallo`). Si aún no llegó a la fase esperada, volver a consultar.

### `GET /bff/cotizaciones/{id}/historia`
Event store del agregado (append-only) y el agregado **reconstruido por replay**:
```json
{"historia": [{"seq":1,"tipo":"CotizacionCreada","version":"v1","fecha":"…","contenido":"{…}"},
              {"seq":2,"tipo":"CotizacionAceptada","version":"v2","fecha":"…","contenido":"{…}"}],
 "reconstruida_por_replay": {"estado":"ACEPTADA","pais":"MX","version":2, ...}}
```
Aquí se ve el Event Sourcing y la evolución de esquema (v1 y v2 en la misma historia).

---

## Comandos directos a otros servicios (base de la saga — Entrega 5)

Cada servicio tiene su propio tópico de comandos; estos endpoints los publican sin pasar por
cotizaciones. Son los que usará el orquestador de la saga.

### `POST /bff/pagos/retener` → `RetenerPago` (tópico `comandos-pago`)
```json
{"id_cotizacion":"<uuid>","id_trabajo":"TRB-001","monto":50000,"moneda":"COP","pais":"CO"}
```
Pagos crea el escrow (idempotente por id de comando) y publica `PagoRetenido`, que trabajos consume.

### `POST /bff/trabajos/agendar` → `AgendarTrabajo` (tópico `comandos-trabajo`)
```json
{"id_trabajo":"TRB-001","id_cotizacion":"<uuid>","id_pago":"<uuid>","pais":"CO","id_proveedor":"PRV-7"}
```
Reglas: `DebeExistirPagoRetenido` (con `id_pago` vacío se rechaza) y `ProveedorDebeTenerDisponibilidad`
(`id_proveedor` = `PRV-SIN-CUPO` produce `TrabajoRechazado`, el evento que hace compensar a la saga).

---

## Consultas por servicio

| Endpoint | Servicio | Devuelve |
|---|---|---|
| `GET /bff/reservas` | pagos | lista de reservas (escrow) `{id, id_cotizacion, id_trabajo, monto, moneda, pais, estado}` |
| `GET /bff/trabajos` | trabajos | lista de agendas `{id, id_trabajo, id_cotizacion, id_pago, pais, estado}` |
| `GET /bff/notificaciones` | notificaciones | lista `{id, tipo, version, destinatario, mensaje, estado}` |

---

## Queries directas de los microservicios (sin BFF)

Existen solo para clientes y para los escenarios de validación; **ningún servicio las usa para
hablar con otro**.

| Servicio | Endpoints |
|---|---|
| cotizaciones :5001 | `GET /health` · `GET /cotizaciones/stats` · `GET /cotizaciones/{id}` · `GET /cotizaciones/{id}/historia` |
| pagos :5002 | `GET /health` · `GET /stats` · `GET /reservas` |
| trabajos :5004 | `GET /health` · `GET /stats` · `GET /trabajos` |
| saga :5005 | `GET /health` · `GET /sagas` · `GET /sagas/stats` · `GET /sagas/{ref}` · `GET /sagas/{ref}/log` · `GET /sagas/log?n=` |
| notificaciones :5003 | `GET /health` · `GET /stats` · `GET /notificaciones` |

---

## Códigos de respuesta

| Código | Significado |
|---|---|
| `202` | comando publicado al tópico (no ejecutado todavía) |
| `200` | query respondida |
| `400` | cuerpo inválido (campos obligatorios faltantes) — validación de forma, no de negocio |
| `404` | el recurso no existe (o el comando que lo crea aún no se procesó / fue rechazado) |
| `503` | un microservicio no responde (el BFF lo reporta, no lo oculta) |
