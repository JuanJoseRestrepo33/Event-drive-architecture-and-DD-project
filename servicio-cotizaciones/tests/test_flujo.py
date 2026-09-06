"""Prueba end-to-end del flujo alineado al tutorial:
comando -> fábrica+reglas -> UoW (batch) -> señal Dominio (módulo pagos +
event store) -> commit -> señal Integracion (despachador -> tópico)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# BD real (PostgreSQL) — el enunciado prohíbe bases de datos de prueba
# tipo SQLite/H2. Se usa la misma instancia del docker-compose; si se
# define DB_URL_TEST se respeta (útil para CI o una BD aparte).
RUTA_LOG = os.path.abspath("test_eventos_integracion.log")
os.environ["DB_URL"] = os.getenv(
    "DB_URL_TEST",
    "postgresql+psycopg2://hda:hda@localhost:5432/cotizaciones")
os.environ["TOPICO_LOG"] = RUTA_LOG

from cotizaciones.api import create_app  # noqa: E402


def _limpiar():
    """Deja el entorno limpio: borra el log del tópico y vacía las tablas
    de la BD real entre pruebas (no se borra el esquema)."""
    if os.path.exists(RUTA_LOG):
        os.remove(RUTA_LOG)

    app = create_app({'TESTING': True})
    with app.app_context():
        from cotizaciones.config.db import db
        from cotizaciones.modulos.pagos.infraestructura.dto import ReservaPago
        from cotizaciones.modulos.cotizaciones.infraestructura.dto import (
            Cotizacion, VisitaCotizacion, EventosCotizacion)
        for modelo in (ReservaPago, EventosCotizacion, VisitaCotizacion,
                       Cotizacion):
            db.session.query(modelo).delete()
        db.session.commit()


def crear_cliente():
    app = create_app({'TESTING': True})
    return app, app.test_client()


def test_flujo_completo():
    _limpiar()
    app, client = crear_cliente()

    # 1. comando CrearCotizacion (lado C de CQS)
    r = client.post("/cotizaciones", json={
        "id_trabajo": "TRB-001", "id_proveedor": "PRV-9",
        "monto": 250000, "moneda": "COP",
        "categoria": "plomeria", "descripcion": "cambio de tuberia",
        "vigencia_desde": "2026-01-01T00:00:00",
        "vigencia_hasta": "2030-01-01T00:00:00"})
    assert r.status_code == 202
    id_cot = r.json["id"]

    # 2. query (lado Q de CQS): retorna DTO, nunca la entidad
    r = client.get(f"/cotizaciones/{id_cot}")
    assert r.status_code == 200 and r.json["estado"] == "EMITIDA"

    # 3. comando AceptarCotizacion (reglas del agregado)
    r = client.post(f"/cotizaciones/{id_cot}/aceptar")
    assert r.status_code == 202 and r.json["estado"] == "ACEPTADA"

    with app.app_context():
        from cotizaciones.config.db import db
        from cotizaciones.modulos.pagos.infraestructura.dto import ReservaPago
        from cotizaciones.modulos.cotizaciones.infraestructura.dto import EventosCotizacion

        # 4. COMUNICACIÓN ENTRE MÓDULOS por eventos de dominio:
        #    pagos reaccionó a la señal CotizacionAceptadaDominio
        reservas = db.session.query(ReservaPago).filter_by(id_cotizacion=id_cot).all()
        assert len(reservas) == 1
        assert reservas[0].estado == "RETENIDO" and reservas[0].monto == 250000

        # 5. EVENT SOURCING: el event store guardó los eventos del agregado
        eventos = db.session.query(EventosCotizacion).filter_by(id_entidad=id_cot).all()
        tipos_store = sorted(e.tipo_evento for e in eventos)
        assert tipos_store == ["CotizacionAceptada", "CotizacionCreada"]
        assert all(e.version == "v1" and e.formato_contenido == "JSON" for e in eventos)
        payload = json.loads(eventos[0].contenido)
        assert payload["id_cotizacion"] == id_cot

    # 6. eventos de INTEGRACIÓN publicados al tópico (señal post-commit)
    lineas = [json.loads(l) for l in open(RUTA_LOG)]
    tipos = [l["type"] for l in lineas]
    assert "CotizacionCreada" in tipos and "CotizacionAceptada" in tipos
    assert all(l["topico"] == "eventos-cotizacion" for l in lineas)
    assert all(l["specversion"] == "v1" for l in lineas)
    assert all(l["service_name"] == "cotizaciones.hda" for l in lineas)


def test_reglas_de_negocio():
    _limpiar()
    app, client = crear_cliente()

    # monto inválido -> MontoDebeSerPositivo rechaza en la fábrica
    r = client.post("/cotizaciones", json={
        "id_trabajo": "TRB-002", "id_proveedor": "PRV-1",
        "monto": -5, "moneda": "COP", "categoria": "x", "descripcion": "y",
        "vigencia_desde": "2026-01-01T00:00:00",
        "vigencia_hasta": "2030-01-01T00:00:00"})
    assert r.status_code == 400

    # aceptar dos veces -> SoloEmitidaSePuedeAceptar rechaza la segunda
    r = client.post("/cotizaciones", json={
        "id_trabajo": "TRB-003", "id_proveedor": "PRV-1",
        "monto": 10, "moneda": "MXN", "categoria": "x", "descripcion": "y",
        "vigencia_desde": "2026-01-01T00:00:00",
        "vigencia_hasta": "2030-01-01T00:00:00"})
    id_cot = r.json["id"]
    assert client.post(f"/cotizaciones/{id_cot}/aceptar").status_code == 202
    assert client.post(f"/cotizaciones/{id_cot}/aceptar").status_code == 400
