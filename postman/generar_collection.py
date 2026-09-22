#!/usr/bin/env python3
"""Genera la collection de Postman del BFF (formato v2.1) y sus environments.
Ejecutar: python postman/generar_collection.py  (desde la raíz del repo)."""
import json
import os
import uuid

AQUI = os.path.dirname(os.path.abspath(__file__))


def req(nombre, metodo, ruta, cuerpo=None, tests=None, pre=None, descripcion=""):
    item = {
        "name": nombre,
        "request": {
            "method": metodo,
            "header": [{"key": "Content-Type", "value": "application/json"}] if cuerpo is not None else [],
            "url": {"raw": "{{base_url}}" + ruta, "host": ["{{base_url}}"],
                    "path": [p for p in ruta.strip("/").split("/")]},
            "description": descripcion,
        },
        "response": [],
    }
    if cuerpo is not None:
        item["request"]["body"] = {"mode": "raw", "raw": json.dumps(cuerpo, indent=2, ensure_ascii=False),
                                   "options": {"raw": {"language": "json"}}}
    eventos = []
    if pre:
        eventos.append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": pre}})
    if tests:
        eventos.append({"listen": "test", "script": {"type": "text/javascript", "exec": tests}})
    if eventos:
        item["event"] = eventos
    return item


T_202 = [
    "pm.test('202 Accepted: el comando fue publicado al tópico', () => pm.response.to.have.status(202));",
    "const b = pm.response.json();",
    "pm.test('respuesta con estado ACEPTADO, id y tópico', () => {",
    "  pm.expect(b.estado).to.eql('ACEPTADO'); pm.expect(b.id).to.be.a('string'); pm.expect(b.topico).to.be.a('string');",
    "});",
]

collection = {
    "info": {
        "_postman_id": str(uuid.uuid4()),
        "name": "Hogar de los Alpes — BFF + Saga (Entrega 5)",
        "description": (
            "Collection para interactuar con la POC a través del BFF (puerto 5000).\n\n"
            "**Cómo se usa el sistema:** las escrituras (POST) publican COMANDOS a Apache Pulsar y "
            "responden `202 Accepted` con el `id` del recurso; el efecto se ve DESPUÉS en las lecturas (GET), "
            "que son queries síncronas compuestas por el BFF. Es CQS + consistencia eventual: tras un POST, "
            "espere ~1-2 s antes del GET (la carpeta *Flujo principal* ya lo hace en los pre-request).\n\n"
            "**Orden recomendado:** ejecute con el Runner las carpetas `1. Transacción larga EXITOSA` y "
            "`2. Transacción larga con FALLO y COMPENSACIÓN` — cada request guarda variables que usan las siguientes. "
            "`POST /bff/cotizaciones/{id}/aceptar` inicia la SAGA orquestada (aceptar → retener pago → agendar trabajo); "
            "`GET /bff/sagas/{id}/log` muestra el SAGA LOG con cada paso y compensación.\n\n"
            "Environments incluidos: `local` (http://localhost:5000) y `gcp` (http://<IP_VM>:5000)."),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "variable": [
        {"key": "base_url", "value": "http://localhost:5000"},
        {"key": "id_cotizacion", "value": ""},
        {"key": "id_pago", "value": ""},
        {"key": "id_trabajo", "value": ""},
        {"key": "id_saga", "value": ""},
        {"key": "id_cotizacion_ko", "value": ""},
        {"key": "id_saga_ko", "value": ""},
    ],
    "item": [],
}

# ------------------------------------------------------------------ 0. salud
collection["item"].append({
    "name": "0. Salud",
    "item": [
        req("Health del BFF y de los 4 servicios", "GET", "/bff/health",
            tests=["pm.test('200: BFF y los 4 microservicios arriba', () => pm.response.to.have.status(200));",
                   "const b = pm.response.json();",
                   "['bff','cotizaciones','pagos','trabajos','notificaciones','saga'].forEach(s => pm.test(s + ' up', () => pm.expect(b[s]).to.eql('up')));"],
            descripcion="El BFF consulta /health de cada microservicio. 503 si alguno está caído (útil durante el escenario E7)."),
        req("Stats (conteos por servicio)", "GET", "/bff/stats",
            tests=["pm.test('200', () => pm.response.to.have.status(200));"],
            descripcion="eventos_en_store (event sourcing en cotizaciones), reservas, trabajos_agendados, notificaciones."),
    ],
})

# ------------------------------------------------------- 1. flujo principal
espera = lambda ms: [f"// espera {ms} ms: el comando anterior se procesa de forma asíncrona (consistencia eventual)",
                     f"setTimeout(() => {{}}, {ms});"]

collection["item"].append({
    "name": "1. Transacción larga EXITOSA (saga orquestada)",
    "description": "Cotización aceptada → pago retenido (escrow) → trabajo agendado. Correr en orden (Runner).",
    "item": [
        req("1.1 Crear cotización  →  COMANDO CrearCotizacion", "POST", "/bff/cotizaciones",
            cuerpo={"id_trabajo": "TRB-{{$randomInt}}", "id_proveedor": "PRV-7",
                    "monto": 220000, "moneda": "MXN", "pais": "MX"},
            tests=T_202 + [
                "pm.collectionVariables.set('id_cotizacion', b.id);",
                "pm.collectionVariables.set('id_trabajo', JSON.parse(pm.request.body.raw).id_trabajo);",
                "pm.test('el comando fue al tópico comandos-cotizacion', () => pm.expect(b.topico).to.eql('comandos-cotizacion'));",
            ],
            descripcion="Publica `CrearCotizacion` en `comandos-cotizacion`. El BFF genera el `id` y lo devuelve en el 202. Proveedor `PRV-7` tiene disponibilidad → la transacción larga terminará bien."),
        req("1.2 Consultar cotización (query → proyección)", "GET", "/bff/cotizaciones/{{id_cotizacion}}",
            pre=espera(1500),
            tests=["pm.test('200: la proyección ya refleja el comando', () => pm.response.to.have.status(200));",
                   "const b = pm.response.json();",
                   "pm.test('estado EMITIDA y version 1', () => { pm.expect(b.estado).to.eql('EMITIDA'); pm.expect(b.version).to.eql(1); });"]),
        req("1.3 Aceptar cotización  →  INICIA LA SAGA (IniciarSagaAceptacion)", "POST",
            "/bff/cotizaciones/{{id_cotizacion}}/aceptar",
            tests=T_202 + [
                "pm.test('el BFF devolvió id_saga y el comando fue a comandos-saga', () => { pm.expect(b.id_saga).to.be.a('string'); pm.expect(b.topico).to.eql('comandos-saga'); });",
                "pm.collectionVariables.set('id_saga', b.id_saga);"],
            descripcion="La capacidad de negocio 'aceptar cotización' ES la transacción larga. El BFF publica `IniciarSagaAceptacion` al orquestador, que envía en orden: `AceptarCotizacion` → `RetenerPago` → `AgendarTrabajo`, esperando el evento de cada paso."),
        req("1.4 Estado de la SAGA (orquestador)", "GET", "/bff/sagas/{{id_saga}}",
            pre=espera(3000),
            tests=["pm.test('200', () => pm.response.to.have.status(200));",
                   "const b = pm.response.json();",
                   "pm.test('saga COMPLETADA', () => pm.expect(b.estado).to.eql('COMPLETADA'));",
                   "pm.test('3 pasos completados en orden', () => pm.expect(b.pasos_completados).to.eql(['ACEPTAR_COTIZACION','RETENER_PAGO','AGENDAR_TRABAJO']));"],
            descripcion="Estado actual de la saga: `estado` ∈ EN_CURSO → COMPLETADA | COMPENSANDO → COMPENSADA. Si aún está EN_CURSO, reenviar (consistencia eventual)."),
        req("1.5 SAGA LOG de la transacción (cada paso, comando y evento)", "GET", "/bff/sagas/{{id_saga}}/log",
            tests=["pm.test('200', () => pm.response.to.have.status(200));",
                   "const b = pm.response.json();",
                   "pm.test('el log empieza en INICIO y termina en FIN COMPLETADA', () => {",
                   "  pm.expect(b.log[0].tipo).to.eql('INICIO'); const u = b.log[b.log.length-1]; pm.expect(u.tipo).to.eql('FIN'); pm.expect(u.mensaje).to.eql('COMPLETADA');",
                   "});",
                   "pm.test('3 PASO_OK y ninguna compensación', () => {",
                   "  pm.expect(b.log.filter(e => e.tipo==='PASO_OK').length).to.eql(3);",
                   "  pm.expect(b.log.filter(e => e.tipo.startsWith('COMPENSACION')).length).to.eql(0);",
                   "});"],
            descripcion="El SAGA LOG es la tabla `saga_log` del orquestador (append-only): una fila por transición — INICIO, COMANDO_ENVIADO, EVENTO_RECIBIDO, PASO_OK/PASO_FALLIDO, COMPENSACION_ENVIADA/OK, FIN — con paso, servicio, mensaje y payload. Consultable también con SQL (docs/SAGA.md)."),
        req("1.6 Estado consolidado del negocio", "GET", "/bff/cotizaciones/{{id_cotizacion}}/estado",
            tests=["pm.test('200', () => pm.response.to.have.status(200));",
                   "const b = pm.response.json();",
                   "pm.test('fase TRABAJO_AGENDADO', () => pm.expect(b.fase).to.eql('TRABAJO_AGENDADO'));",
                   "pm.test('pago RETENIDO y trabajo AGENDADO', () => { pm.expect(b.pago.estado).to.eql('RETENIDO'); pm.expect(b.trabajo.estado).to.eql('AGENDADO'); });",
                   "pm.collectionVariables.set('id_pago', b.pago.id);"],
            descripcion="Vista compuesta por el BFF: cotización + pago + trabajo + notificaciones + resumen de la saga."),
        req("1.7 Historia del agregado (event sourcing)", "GET", "/bff/cotizaciones/{{id_cotizacion}}/historia",
            tests=["pm.test('200', () => pm.response.to.have.status(200));",
                   "const b = pm.response.json();",
                   "pm.test('eventos: Creada v1, Aceptada v2', () => pm.expect(b.historia.map(e => e.tipo)).to.eql(['CotizacionCreada','CotizacionAceptada']));"]),
    ],
})

collection["item"].append({
    "name": "2. Transacción larga con FALLO y COMPENSACIÓN",
    "description": "El proveedor PRV-SIN-CUPO no tiene disponibilidad: trabajos rechaza el agendamiento y la saga compensa en orden inverso (libera el pago, revierte la aceptación).",
    "item": [
        req("2.1 Crear cotización con proveedor SIN CUPO", "POST", "/bff/cotizaciones",
            cuerpo={"id_trabajo": "TRB-KO-{{$randomInt}}", "id_proveedor": "PRV-SIN-CUPO",
                    "monto": 150000, "moneda": "COP", "pais": "CO"},
            tests=T_202 + ["pm.collectionVariables.set('id_cotizacion_ko', b.id);"],
            descripcion="Regla de negocio del núcleo (trabajos): `ProveedorDebeTenerDisponibilidad`. `PRV-SIN-CUPO` la incumple → el paso 3 de la saga fallará."),
        req("2.2 Aceptar  →  INICIA LA SAGA (fallará en el paso 3)", "POST",
            "/bff/cotizaciones/{{id_cotizacion_ko}}/aceptar",
            pre=espera(1500),
            tests=T_202 + ["pm.collectionVariables.set('id_saga_ko', b.id_saga);"]),
        req("2.3 Estado de la SAGA → COMPENSADA", "GET", "/bff/sagas/{{id_saga_ko}}",
            pre=espera(4000),
            tests=["pm.test('200', () => pm.response.to.have.status(200));",
                   "const b = pm.response.json();",
                   "pm.test('saga COMPENSADA (no COMPLETADA)', () => pm.expect(b.estado).to.eql('COMPENSADA'));",
                   "pm.test('motivo del fallo registrado', () => pm.expect(b.motivo_fallo).to.include('disponibilidad'));",
                   "pm.test('ningún paso queda completado tras compensar', () => pm.expect(b.pasos_completados).to.eql([]));"],
            descripcion="Si aún dice COMPENSANDO, reenviar: las compensaciones viajan por Pulsar y se confirman por eventos."),
        req("2.4 SAGA LOG con las compensaciones en orden inverso", "GET", "/bff/sagas/{{id_saga_ko}}/log",
            tests=["pm.test('200', () => pm.response.to.have.status(200));",
                   "const b = pm.response.json(); const tipos = b.log.map(e => e.tipo);",
                   "pm.test('PASO_FALLIDO en AGENDAR_TRABAJO', () => { const f = b.log.find(e => e.tipo==='PASO_FALLIDO'); pm.expect(f.paso).to.eql('AGENDAR_TRABAJO'); pm.expect(f.mensaje).to.eql('TrabajoRechazado'); });",
                   "pm.test('compensaciones en orden inverso: pago primero, luego cotización', () => {",
                   "  const c = b.log.filter(e => e.tipo==='COMPENSACION_ENVIADA').map(e => e.mensaje);",
                   "  pm.expect(c).to.eql(['RevertirPago','RevertirAceptacion']);",
                   "});",
                   "pm.test('ambas compensaciones confirmadas (COMPENSACION_OK x2) y FIN COMPENSADA', () => {",
                   "  pm.expect(b.log.filter(e => e.tipo==='COMPENSACION_OK').length).to.eql(2);",
                   "  pm.expect(b.log[b.log.length-1].mensaje).to.eql('COMPENSADA');",
                   "});"],
            descripcion="Secuencia esperada: INICIO → (AceptarCotizacion ✓) → (RetenerPago ✓) → AgendarTrabajo ✗ TrabajoRechazado → RevertirPago → PagoRevertido ✓ → RevertirAceptacion → CotizacionRevertida ✓ → FIN COMPENSADA."),
        req("2.5 Estado consolidado: sistema consistente tras compensar", "GET", "/bff/cotizaciones/{{id_cotizacion_ko}}/estado",
            tests=["pm.test('200', () => pm.response.to.have.status(200));",
                   "const b = pm.response.json();",
                   "pm.test('fase COMPENSADA', () => pm.expect(b.fase).to.eql('COMPENSADA'));",
                   "pm.test('cotización volvió a EMITIDA', () => pm.expect(b.cotizacion.estado).to.eql('EMITIDA'));",
                   "pm.test('pago LIBERADO (escrow devuelto)', () => pm.expect(b.pago.estado).to.eql('LIBERADO'));",
                   "pm.test('trabajo RECHAZADO', () => pm.expect(b.trabajo.estado).to.eql('RECHAZADO'));"]),
        req("2.6 Historia event-sourced: la compensación es un evento más", "GET", "/bff/cotizaciones/{{id_cotizacion_ko}}/historia",
            tests=["const b = pm.response.json();",
                   "pm.test('Creada → Aceptada → Revertida (nunca se borra historia)', () => pm.expect(b.historia.map(e => e.tipo)).to.eql(['CotizacionCreada','CotizacionAceptada','CotizacionRevertida']));",
                   "pm.test('replay reconstruye EMITIDA', () => pm.expect(b.reconstruida_por_replay.estado).to.eql('EMITIDA'));"]),
    ],
})

collection["item"].append({
    "name": "3. Monitoreo de sagas (Saga Log)",
    "item": [
        req("Todas las sagas y conteo por estado", "GET", "/bff/sagas",
            tests=["pm.test('200', () => pm.response.to.have.status(200));",
                   "const b = pm.response.json();",
                   "pm.test('hay al menos una COMPLETADA y una COMPENSADA', () => { pm.expect(b.por_estado.COMPLETADA).to.be.at.least(1); pm.expect(b.por_estado.COMPENSADA).to.be.at.least(1); });"],
            descripcion="Equivale a `SELECT estado, COUNT(*) FROM sagas GROUP BY estado`."),
        req("Últimas 30 entradas del Saga Log (todas las sagas)", "GET", "/bff/sagas/log?n=30",
            tests=["pm.test('200', () => pm.response.to.have.status(200));"],
            descripcion="Equivale a `SELECT * FROM saga_log ORDER BY id DESC LIMIT 30`."),
        req("Saga por id de cotización", "GET", "/bff/sagas/{{id_cotizacion}}",
            tests=["pm.test('200: se puede buscar por id_cotizacion o por id_saga', () => pm.response.to.have.status(200));"]),
    ],
})

# --------------------------------------------------------- 2. consultas
collection["item"].append({
    "name": "4. Consultas por servicio",
    "item": [
        req("Reservas de pago (servicio pagos)", "GET", "/bff/reservas",
            tests=["pm.test('200', () => pm.response.to.have.status(200));",
                   "pm.test('contiene la reserva del flujo exitoso (RETENIDO) y la del compensado (LIBERADO)', () => { const r = pm.response.json(); pm.expect(r.some(x => x.id_cotizacion === pm.collectionVariables.get('id_cotizacion') && x.estado==='RETENIDO')).to.be.true; pm.expect(r.some(x => x.id_cotizacion === pm.collectionVariables.get('id_cotizacion_ko') && x.estado==='LIBERADO')).to.be.true; });"]),
        req("Trabajos agendados (servicio trabajos)", "GET", "/bff/trabajos",
            tests=["pm.test('200', () => pm.response.to.have.status(200));",
                   "pm.test('contiene el trabajo del flujo', () => pm.expect(pm.response.json().some(t => t.id_cotizacion === pm.collectionVariables.get('id_cotizacion'))).to.be.true);"]),
        req("Notificaciones (servicio notificaciones)", "GET", "/bff/notificaciones",
            tests=["pm.test('200', () => pm.response.to.have.status(200));",
                   "pm.test('hay notificaciones v1 y v2 (consumidor v1 tolerante)', () => { const v = new Set(pm.response.json().map(n => n.version)); pm.expect(v.has('v1') || v.has('v2')).to.be.true; });"]),
    ],
})

# ------------------------------------------ 3. comandos directos (saga E5)
collection["item"].append({
    "name": "5. Comandos directos a servicios (lo que hace el orquestador)",
    "description": "Cada servicio tiene su propio tópico de comandos. Estos endpoints los publican directamente, igual que hace el orquestador.",
    "item": [
        req("Retener pago  →  COMANDO RetenerPago (tópico comandos-pago)", "POST", "/bff/pagos/retener",
            cuerpo={"id_cotizacion": "{{$guid}}", "id_trabajo": "TRB-DIRECTO-{{$randomInt}}",
                    "monto": 50000, "moneda": "COP", "pais": "CO"},
            tests=T_202 + ["pm.test('tópico comandos-pago', () => pm.expect(b.topico).to.eql('comandos-pago'));"],
            descripcion="Publica `RetenerPago` sin pasar por cotizaciones. Pagos crea el escrow y publica `PagoRetenido` → trabajos agenda."),
        req("Agendar trabajo  →  COMANDO AgendarTrabajo (tópico comandos-trabajo)", "POST", "/bff/trabajos/agendar",
            cuerpo={"id_trabajo": "TRB-DIRECTO-{{$randomInt}}", "id_cotizacion": "{{$guid}}",
                    "id_pago": "{{$guid}}", "pais": "AR"},
            tests=T_202 + ["pm.test('tópico comandos-trabajo', () => pm.expect(b.topico).to.eql('comandos-trabajo'));"]),
        req("Agendar trabajo SIN pago → rechazado por regla DebeExistirPagoRetenido", "POST", "/bff/trabajos/agendar",
            cuerpo={"id_trabajo": "TRB-SIN-PAGO", "id_cotizacion": "{{$guid}}", "id_pago": "", "pais": "CO"},
            tests=T_202 + ["// 202 (aceptado para procesar); trabajos lo rechaza: ver logs 'RECHAZADO por regla'"]),
    ],
})

# ----------------------------------------------------- 4. errores
collection["item"].append({
    "name": "6. Validaciones y errores",
    "item": [
        req("Crear cotización sin campos → 400", "POST", "/bff/cotizaciones", cuerpo={"monto": 1},
            tests=["pm.test('400 Bad Request', () => pm.response.to.have.status(400));"]),
        req("Cotización inexistente → 404", "GET", "/bff/cotizaciones/00000000-0000-0000-0000-000000000000",
            tests=["pm.test('404 Not Found', () => pm.response.to.have.status(404));"]),
        req("Monto negativo → 202 pero RECHAZADO por regla MontoDebeSerPositivo", "POST", "/bff/cotizaciones",
            cuerpo={"id_trabajo": "TRB-NEG", "id_proveedor": "PRV-1", "monto": -5, "moneda": "COP"},
            tests=T_202 + ["pm.collectionVariables.set('id_rechazada', b.id);"],
            descripcion="El BFF no valida reglas de negocio (pertenecen al dominio). Cotizaciones rechaza el comando; el recurso nunca existe (ver siguiente request)."),
        req("La cotización rechazada no existe → 404", "GET", "/bff/cotizaciones/{{id_rechazada}}",
            pre=espera(1500),
            tests=["pm.test('404: la regla del dominio impidió crearla', () => pm.response.to.have.status(404));"]),
    ],
})

# ----------------------------------------------------- escribir
os.makedirs(AQUI, exist_ok=True)
with open(os.path.join(AQUI, "HogarDeLosAlpes-BFF.postman_collection.json"), "w", encoding="utf-8") as f:
    json.dump(collection, f, indent=2, ensure_ascii=False)

for nombre, url in (("local", "http://localhost:5000"), ("gcp", "http://<IP_PUBLICA_VM>:5000")):
    env = {"id": str(uuid.uuid4()), "name": f"HdA {nombre}",
           "values": [{"key": "base_url", "value": url, "enabled": True}],
           "_postman_variable_scope": "environment"}
    with open(os.path.join(AQUI, f"HdA-{nombre}.postman_environment.json"), "w", encoding="utf-8") as f:
        json.dump(env, f, indent=2, ensure_ascii=False)

print("collection + environments generados en", AQUI)
