"""Contratos de mensajes usados por los ESCENARIOS (cliente que simula al
BFF/partner). Mismo envelope que los servicios: id, time, specversion,
type, class, data. Los esquemas de los servicios viven en cada
`modulos/<bc>/infraestructura/schema/v{1,2}/`."""
import time
import uuid


def _base(tipo, clase, spec):
    return {"id": str(uuid.uuid4()), "time": int(time.time() * 1000), "specversion": spec,
            "type": tipo, "class": clase, "service_source": "cliente-escenarios"}


def comando_crear_cotizacion(id_trabajo, id_proveedor, monto, moneda, pais="CO"):
    m = _base("CrearCotizacion", "comando", "v1")
    m["data"] = {"id_trabajo": id_trabajo, "id_proveedor": id_proveedor,
                 "monto": monto, "moneda": moneda, "pais": pais}
    return m


def comando_aceptar_cotizacion(id_cotizacion):
    m = _base("AceptarCotizacion", "comando", "v1")
    m["data"] = {"id_cotizacion": id_cotizacion}
    return m


def evento_cotizacion_aceptada_v1(id_cotizacion, id_trabajo, id_proveedor, monto, moneda):
    m = _base("CotizacionAceptada", "evento", "v1")
    m["data"] = {"id_cotizacion": id_cotizacion, "id_trabajo": id_trabajo,
                 "id_proveedor": id_proveedor, "monto": monto, "moneda": moneda}
    return m


def evento_cotizacion_aceptada_v2(id_cotizacion, id_trabajo, id_proveedor, monto, moneda, pais):
    m = _base("CotizacionAceptada", "evento", "v2")
    m["data"] = {"id_cotizacion": id_cotizacion, "id_trabajo": id_trabajo,
                 "id_proveedor": id_proveedor, "monto": monto, "moneda": moneda, "pais": pais}
    return m
