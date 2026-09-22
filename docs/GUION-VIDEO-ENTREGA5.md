# Guion del video de sustentación — Entrega 5

Duración objetivo: **14–15 minutos**. Una pantalla (VS Code + 2 terminales + Postman), tres voces.
Hilo conductor: **una transacción larga que termina bien y otra que falla y se compensa**, vistas
en el código, en Postman, en los logs y en el **Saga Log por SQL**.

Regla de oro: nunca afirmar algo que la pantalla no muestre.

---

## 0. Preparación (antes de grabar)

```bash
docker compose down -v && docker compose up --build -d && docker compose build escenarios
curl -s localhost:5000/bff/health      # los 7 "up"
```
- **Terminal A** (logs filtrados):
  `docker compose logs -f saga cotizaciones pagos trabajos | grep -E "\[saga\]|\[cotizaciones\] (COMANDO|EVENTO)|\[pagos\] (CONSUMIDO|EVENTO)|\[trabajos\] (CONSUMIDO|EVENTO)"`
- **Terminal B**: comandos (raíz del repo).
- **Postman**: collection importada, environment `HdA local`, carpetas 1 y 2 listas para el Runner.
- **VS Code**, pestañas en este orden:
  1. `docs/img/R1-mapa-contexto-refinado.png`
  2. `servicios/saga/src/saga/modulos/saga/dominio/objetos_valor.py` (la `DEFINICION` de pasos)
  3. `servicios/saga/src/saga/modulos/saga/dominio/entidades.py` (agregado `Saga`)
  4. `servicios/saga/src/saga/modulos/saga/aplicacion/comandos/base.py` (`persistir_y_despachar`)
  5. `servicios/saga/src/saga/modulos/saga/infraestructura/dto.py` (tablas `sagas`, `saga_log`)
  6. `servicios/trabajos/src/trabajos/modulos/trabajos/aplicacion/comandos/agendar_trabajo.py`
  7. `servicios/pagos/src/pagos/modulos/pagos/dominio/entidades.py` (`revertir`)
  8. `servicios/bff/src/bff/api/__init__.py` (endpoint `aceptar`)

---

## 1. Arquitectura y decisión de orquestación — 2:00 (miembro 1)

Pestaña 1 (mapa de contexto refinado). Señalar los Δ ámbar.
> "Cuatro microservicios por contexto acotado, Pulsar como único medio de comunicación, un BFF como
> única puerta síncrona y, nuevo en esta entrega, un **contexto de Transacciones**: el orquestador
> de la saga *aceptar cotización* — aceptar, retener el pago en escrow, agendar el trabajo — con
> su **Saga Log**."

Decisión (30 s): *"Elegimos **orquestación** por tres razones de negocio: con 30 partners y SLAs,
soporte necesita saber en una consulta en qué paso está una transacción y por qué falló — el
estado vive en un solo lugar; las compensaciones tienen orden (liberar el escrow antes de revertir
la aceptación); y agregar un paso para la expansión global es una línea en la definición. El
orquestador no tiene reglas de negocio: solo secuencia. Notificaciones sigue en coreografía porque
no participa en la transacción."*

---

## 2. Código de la saga — 3:30 (miembro 2)

**Pestaña 2 — `DEFINICION`**: *"La transacción es una tabla declarativa: para cada paso, el comando,
el tópico, el evento que lo confirma, el que lo falla y la compensación."*

**Pestaña 3 — agregado `Saga`**: señalar `iniciar`, `aplicar_evento` (avanza / termina /
compensa), `_compensar_siguiente` (orden inverso: `reversed(pasos_completados)`), y `_log`: *"cada
transición agrega un evento de dominio `EntradaSagaLog` — el Saga Log es el modelo, no un print."*

**Pestaña 4 — `persistir_y_despachar`**: *"estado de la saga + filas del log + marca de idempotencia
en una sola Unidad de Trabajo; después del commit se publican los comandos. Si hay fila, el estado
cambió, y viceversa. Si el orquestador cae, al volver reanuda desde la base."*

**Pestaña 5 — tablas**: `sagas` y `saga_log` (tipos de entrada).

**Pestaña 6 — trabajos**: la regla `ProveedorDebeTenerDisponibilidad`: *"el fallo de negocio se
modela en el dominio del servicio: si no cumple, el agregado se registra RECHAZADO y emite
`TrabajoRechazado`. El orquestador solo reacciona."*

**Pestaña 7 — pagos `revertir`**: *"la compensación es comportamiento del agregado con su
invariante (solo un pago RETENIDO se libera) y su evento `PagoRevertido`."* Mencionar que en
cotizaciones `CotizacionRevertida` es un evento más del event store (nunca se borra historia).

**Pestaña 8 — BFF**: `POST /bff/cotizaciones/{id}/aceptar` publica `IniciarSagaAceptacion` a
`comandos-saga` y responde 202 con `id_saga`.

---

## 3. Transacción exitosa en Postman — 2:00 (miembro 3)

Runner sobre la carpeta **1**. Señalar en orden: `1.3` → 202 con `id_saga`; en Terminal A las
líneas `[saga] COMANDO AceptarCotizacion → 'comandos-cotizacion'` … `[saga] saga … ← TrabajoAgendado
⇒ estado COMPLETADA`; `1.4` → `COMPLETADA` con los tres pasos; `1.5` → el Saga Log de 11 entradas;
`1.6` → `fase: TRABAJO_AGENDADO`.

---

## 4. Transacción con fallo y compensación — 3:00 (miembro 3)

Runner sobre la carpeta **2** (proveedor `PRV-SIN-CUPO`). Narrar con Terminal A visible:
1. `[trabajos] EVENTO TrabajoRechazado v1 publicado` → *"el paso 3 falló por una regla de negocio"*.
2. `[saga] COMPENSACIÓN RevertirPago → 'comandos-pago'` → `[pagos] EVENTO PagoRevertido` →
   *"primera compensación: se libera el escrow"*.
3. `[saga] COMPENSACIÓN RevertirAceptacion → 'comandos-cotizacion'` → `[cotizaciones] EVENTO
   CotizacionRevertida` → *"segunda: la aceptación se revierte"*.
4. `[saga] … ⇒ estado COMPENSADA`.
5. `2.4` en Postman: el Saga Log con `PASO_FALLIDO` y las dos `COMPENSACION_ENVIADA/OK` en orden
   inverso; `2.5`: EMITIDA · LIBERADO · RECHAZADO; `2.6`: historia `Creada → Aceptada → Revertida`.

---

## 5. Saga Log con cliente SQL — 1:30 (miembro 1)

Terminal B:
```bash
docker compose exec saga sqlite3 -header -column /app/src/saga/api/saga.db
```
```sql
SELECT estado, COUNT(*) AS sagas FROM sagas GROUP BY estado;
SELECT substr(id,1,8) saga, estado, paso_actual, motivo_fallo FROM sagas ORDER BY fecha_inicio DESC LIMIT 5;
SELECT secuencia, tipo, paso, servicio, mensaje FROM saga_log WHERE id_saga='<id de la compensada>' ORDER BY secuencia;
SELECT paso, mensaje, COUNT(*) FROM saga_log WHERE tipo='PASO_FALLIDO' GROUP BY paso, mensaje;
```
> "Esto es lo que vería soporte durante un incidente: cuántas transacciones hay en cada estado, en
> qué paso están y por qué fallaron."

---

## 6. Experimentación y resultados — 2:00 (miembro 2)

Abrir `Entrega5-Resultados-Experimentacion.pdf`, tabla de E1: *"0 rechazos en 30/300/1.000;
drenaje lineal, 37 transacciones por segundo por réplica sin escalar; hipótesis cumplida."* E7:
*"núcleo 100 % con pagos caído, 50/50 sagas completadas al volver, 0 duplicados con re-entregas
inyectadas."* E6: *"v1 y v2 conviven; y en esta entrega el contrato creció seis mensajes sin romper
nada."* Opcional en vivo (si hay tiempo): `docker compose run --rm -e N=300 escenarios python
escenario_e1_escalabilidad.py`.

---

## 7. Refinamiento de la arquitectura — 1:30 (miembro 1)

`Entrega5-Refinamiento-Arquitectura.pdf`, tabla "Qué aprendimos y qué cambió": cada resultado →
cambio (Δ). Mostrar R4 (C&C refinado) y cerrar: *"ningún cambio acopló dos contextos: solo agregamos
un contexto, agregados y eventos — la partición de la Entrega 1 era la correcta."*

Cierre: link del repo, `README-GCP.md` con el despliegue, Postman contra la IP de la VM.

---

## Preguntas probables

- **¿Por qué no coreografía?** Visibilidad (Saga Log en un lugar), orden de compensaciones,
  evolución de la transacción; sin lógica de dominio en el orquestador.
- **¿Qué pasa si cae el orquestador?** Los mensajes esperan en Pulsar; el estado está en `sagas`;
  al volver reanuda desde `paso_actual`. Lo que no hay aún: timeouts → `FALLIDA` (trabajo futuro).
- **¿Y si el orquestador recibe dos veces el mismo evento?** `eventos_procesados`: lo ignora
  (E7 lo inyecta y lo verifica).
- **¿Por qué la compensación no borra la aceptación?** Event sourcing: la historia es inmutable;
  `CotizacionRevertida` deja rastro de que hubo una aceptación y por qué se deshizo.
- **¿Cómo se fuerza el fallo?** Regla de disponibilidad del proveedor (`PRV-SIN-CUPO`, configurable);
  es un fallo de negocio realista, no un `raise` artificial.
