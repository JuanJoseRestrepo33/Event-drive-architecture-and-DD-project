"""Consumidores del broker (estilo tutorial).

ORQUESTACIÓN (Entrega 5): trabajos reacciona ÚNICAMENTE a COMANDOS de su
tópico `comandos-trabajo` (AgendarTrabajo), publicados por el orquestador
de la saga. Responde con TrabajoAgendado o TrabajoRechazado (eventos)."""
from trabajos.seedwork.aplicacion.comandos import ejecutar_commando
from trabajos.seedwork.dominio.excepciones import ExcepcionDominio
from trabajos.seedwork.infraestructura.broker import broker
from ..aplicacion.comandos.agendar_trabajo import AgendarTrabajo


def _a_comando(mensaje: dict):
    d = mensaje.get("data", {})
    if mensaje.get("type") == "AgendarTrabajo":
        return AgendarTrabajo(id_evento_origen=mensaje["id"], id_trabajo=d["id_trabajo"],
                              id_cotizacion=d["id_cotizacion"], id_pago=d["id_pago"],
                              pais=d.get("pais", "CO"), id_proveedor=d.get("id_proveedor", ""))
    return None


def _handler(app):
    def handler(mensaje):
        comando = _a_comando(mensaje)
        if comando is None:
            return
        with app.test_request_context():
            try:
                resultado = ejecutar_commando(comando)
                if resultado != "DUPLICADO":
                    print(f"[trabajos] CONSUMIDO COMANDO {mensaje.get('type')} -> {resultado}")
            except ExcepcionDominio as e:
                print(f"[trabajos] {mensaje.get('type')} RECHAZADO por regla: {e}")
    return handler


def suscribirse_a_comandos(app):
    broker().consumir("comandos-trabajo", "trabajos-sub-comandos", _handler(app))
