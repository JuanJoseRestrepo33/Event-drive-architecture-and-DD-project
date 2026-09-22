"""Objetos valor del dominio de la saga."""
from enum import Enum


class EstadoSaga(str, Enum):
    EN_CURSO = "EN_CURSO"
    COMPLETADA = "COMPLETADA"        # todos los pasos OK
    COMPENSANDO = "COMPENSANDO"      # un paso falló; deshaciendo los anteriores
    COMPENSADA = "COMPENSADA"        # compensación terminada: sistema consistente
    FALLIDA = "FALLIDA"              # no se pudo ni completar ni compensar (intervención manual)


class Paso(str, Enum):
    """Pasos de la transacción larga 'aceptar cotización' en orden."""
    ACEPTAR_COTIZACION = "ACEPTAR_COTIZACION"
    RETENER_PAGO = "RETENER_PAGO"
    AGENDAR_TRABAJO = "AGENDAR_TRABAJO"


class TipoEntrada(str, Enum):
    """Tipos de entrada del Saga Log."""
    INICIO = "INICIO"
    COMANDO_ENVIADO = "COMANDO_ENVIADO"
    EVENTO_RECIBIDO = "EVENTO_RECIBIDO"
    PASO_OK = "PASO_OK"
    PASO_FALLIDO = "PASO_FALLIDO"
    COMPENSACION_ENVIADA = "COMPENSACION_ENVIADA"
    COMPENSACION_OK = "COMPENSACION_OK"
    FIN = "FIN"


# Orden de los pasos y, para cada uno, el comando que lo ejecuta, el evento que
# lo confirma, el evento que lo falla y la compensación (comando + evento).
DEFINICION = [
    {"paso": Paso.ACEPTAR_COTIZACION, "servicio": "cotizaciones",
     "comando": "AceptarCotizacion", "topico": "comandos-cotizacion",
     "evento_ok": "CotizacionAceptada", "evento_fallo": None,
     "compensacion": "RevertirAceptacion", "evento_compensado": "CotizacionRevertida"},
    {"paso": Paso.RETENER_PAGO, "servicio": "pagos",
     "comando": "RetenerPago", "topico": "comandos-pago",
     "evento_ok": "PagoRetenido", "evento_fallo": None,
     "compensacion": "RevertirPago", "evento_compensado": "PagoRevertido"},
    {"paso": Paso.AGENDAR_TRABAJO, "servicio": "trabajos",
     "comando": "AgendarTrabajo", "topico": "comandos-trabajo",
     "evento_ok": "TrabajoAgendado", "evento_fallo": "TrabajoRechazado",
     "compensacion": None, "evento_compensado": None},
]
