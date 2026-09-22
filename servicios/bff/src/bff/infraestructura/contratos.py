"""Contratos de COMANDOS que el BFF publica a los tópicos de Pulsar.

Mismo envelope que usan los servicios (id, time, specversion, type, class,
service_source, data). El BFF NO define eventos: solo emite intenciones; los
hechos los publican los servicios dueños de cada contexto acotado.
"""
import time
import uuid


def _base(tipo, spec="v1"):
    return {"id": str(uuid.uuid4()), "time": int(time.time() * 1000), "specversion": spec,
            "type": tipo, "class": "comando", "service_source": "bff"}


def crear_cotizacion(id_cotizacion, id_trabajo, id_proveedor, monto, moneda, pais="CO"):
    m = _base("CrearCotizacion")
    m["data"] = {"id_cotizacion": id_cotizacion, "id_trabajo": id_trabajo,
                 "id_proveedor": id_proveedor, "monto": monto, "moneda": moneda, "pais": pais}
    return m


def aceptar_cotizacion(id_cotizacion):
    m = _base("AceptarCotizacion")
    m["data"] = {"id_cotizacion": id_cotizacion}
    return m


def retener_pago(id_cotizacion, id_trabajo, monto, moneda, pais="CO"):
    m = _base("RetenerPago")
    m["data"] = {"id_cotizacion": id_cotizacion, "id_trabajo": id_trabajo,
                 "monto": monto, "moneda": moneda, "pais": pais}
    return m


def agendar_trabajo(id_trabajo, id_cotizacion, id_pago, pais="CO"):
    m = _base("AgendarTrabajo")
    m["data"] = {"id_trabajo": id_trabajo, "id_cotizacion": id_cotizacion,
                 "id_pago": id_pago, "pais": pais}
    return m


def iniciar_saga_aceptacion(id_saga, id_cotizacion, datos):
    m = _base("IniciarSagaAceptacion")
    m["data"] = {"id_saga": id_saga, "id_cotizacion": id_cotizacion, "datos": datos}
    return m
