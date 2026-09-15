"""Consumidores del broker (estilo tutorial): el servicio se suscribe al
tópico de COMANDOS `comandos-cotizacion`, traduce el mensaje al comando de
aplicación y lo ejecuta con `ejecutar_commando`. Corre en un hilo; usa un
contexto de request de Flask para que la Unidad de Trabajo (patrón del
tutorial, guardada en la sesión) funcione fuera del ciclo HTTP."""
from cotizaciones.seedwork.aplicacion.comandos import ejecutar_commando
from cotizaciones.seedwork.dominio.excepciones import ExcepcionDominio
from cotizaciones.seedwork.infraestructura.broker import broker
from ..aplicacion.comandos.crear_cotizacion import CrearCotizacion
from ..aplicacion.comandos.aceptar_cotizacion import AceptarCotizacion


def _a_comando(mensaje: dict):
    d = mensaje.get("data", {})
    if mensaje.get("type") == "CrearCotizacion":
        return CrearCotizacion(id_trabajo=d["id_trabajo"], id_proveedor=d["id_proveedor"],
                               monto=d["monto"], moneda=d["moneda"], pais=d.get("pais", "CO"))
    if mensaje.get("type") == "AceptarCotizacion":
        return AceptarCotizacion(id_cotizacion=d["id_cotizacion"])
    return None


def suscribirse_a_comandos(app):
    def handler(mensaje):
        comando = _a_comando(mensaje)
        if comando is None:
            return
        with app.test_request_context():
            try:
                resultado = ejecutar_commando(comando)
                print(f"[cotizaciones] COMANDO {mensaje['type']} -> {resultado}")
            except ExcepcionDominio as e:
                print(f"[cotizaciones] COMANDO {mensaje['type']} RECHAZADO por regla: {e}")

    broker().consumir("comandos-cotizacion", "cotizaciones-sub-comandos", handler)
