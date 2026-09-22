"""DOMINIO del orquestador: el agregado Saga.

La Saga es la máquina de estados de la transacción larga "aceptar cotización"
(3 servicios: cotizaciones -> pagos -> trabajos). Sabe:
- en qué paso va, con qué datos (los que necesita cada comando siguiente),
- qué comando enviar a continuación (`siguiente_comando`),
- qué hacer cuando llega un evento (`aplicar_evento`): avanzar, terminar o
  empezar a compensar en orden inverso,
- y registra CADA transición como una entrada del SAGA LOG (eventos de
  dominio `EntradaSagaLog`), que la infraestructura persiste.

No conoce Flask, SQLAlchemy ni el broker.
"""
from dataclasses import dataclass, field
from datetime import datetime
import json

from saga.seedwork.dominio.entidades import AgregacionRaiz
from saga.seedwork.dominio.eventos import EventoDominio
from .objetos_valor import EstadoSaga, Paso, TipoEntrada, DEFINICION


class SagaTerminada(Exception):
    ...


@dataclass
class EntradaSagaLog(EventoDominio):
    """Una línea del Saga Log (evento de dominio del agregado Saga)."""
    id_saga: str = None
    secuencia: int = 0
    tipo: str = None            # TipoEntrada
    paso: str = None            # Paso o None
    servicio: str = None
    mensaje: str = None         # nombre del comando/evento
    detalle: str = None         # texto legible
    payload: str = None         # JSON


@dataclass
class ComandoPendiente:
    """Comando que la saga decidió enviar (lo publica la infraestructura)."""
    tipo: str
    topico: str
    data: dict
    es_compensacion: bool = False


@dataclass
class Saga(AgregacionRaiz):
    id_cotizacion: str = field(default=None)
    estado: EstadoSaga = field(default=EstadoSaga.EN_CURSO)
    paso_actual: str = field(default=None)        # Paso en curso (esperando su evento)
    pasos_completados: list = field(default_factory=list)   # en orden
    datos: dict = field(default_factory=dict)      # contexto acumulado (montos, ids...)
    secuencia: int = field(default=0)
    motivo_fallo: str = field(default=None)
    fecha_inicio: datetime = field(default_factory=datetime.utcnow)
    fecha_fin: datetime = field(default=None)
    comandos_pendientes: list = field(default_factory=list)

    # ------------------------------------------------------------ log
    def _log(self, tipo: TipoEntrada, paso=None, servicio=None, mensaje=None, detalle=None, payload=None):
        self.secuencia += 1
        self.agregar_evento(EntradaSagaLog(
            id_saga=str(self.id), secuencia=self.secuencia, tipo=tipo.value,
            paso=paso.value if isinstance(paso, Paso) else paso, servicio=servicio,
            mensaje=mensaje, detalle=detalle,
            payload=json.dumps(payload, ensure_ascii=False) if payload is not None else None))

    # ------------------------------------------------------------ inicio
    def iniciar(self, id_cotizacion: str, datos_iniciales: dict):
        self.id_cotizacion = id_cotizacion
        self.datos = dict(datos_iniciales or {})
        self.datos["id_cotizacion"] = id_cotizacion
        self.estado = EstadoSaga.EN_CURSO
        self._log(TipoEntrada.INICIO, servicio="saga", mensaje="IniciarSagaAceptacion",
                  detalle=f"Transacción larga iniciada para la cotización {id_cotizacion[:8]}…",
                  payload=self.datos)
        self._enviar_paso(DEFINICION[0])

    # ------------------------------------------------------------ pasos
    def _definicion(self, paso: str):
        return next(d for d in DEFINICION if d["paso"].value == paso)

    def _enviar_paso(self, defn):
        self.paso_actual = defn["paso"].value
        data = self._datos_para(defn["comando"])
        self.comandos_pendientes.append(ComandoPendiente(defn["comando"], defn["topico"], data))
        self._log(TipoEntrada.COMANDO_ENVIADO, paso=defn["paso"], servicio=defn["servicio"],
                  mensaje=defn["comando"], detalle=f"Comando {defn['comando']} → {defn['topico']}", payload=data)

    def _datos_para(self, comando: str) -> dict:
        d = self.datos
        if comando == "AceptarCotizacion":
            return {"id_cotizacion": d["id_cotizacion"]}
        if comando == "RetenerPago":
            return {"id_cotizacion": d["id_cotizacion"], "id_trabajo": d.get("id_trabajo"),
                    "monto": d.get("monto"), "moneda": d.get("moneda"), "pais": d.get("pais", "CO")}
        if comando == "AgendarTrabajo":
            return {"id_trabajo": d.get("id_trabajo"), "id_cotizacion": d["id_cotizacion"],
                    "id_pago": d.get("id_pago"), "pais": d.get("pais", "CO"),
                    "id_proveedor": d.get("id_proveedor", "")}
        if comando == "RevertirPago":
            return {"id_cotizacion": d["id_cotizacion"], "motivo": self.motivo_fallo}
        if comando == "RevertirAceptacion":
            return {"id_cotizacion": d["id_cotizacion"], "motivo": self.motivo_fallo}
        return {}

    # ------------------------------------------------------------ eventos
    def aplicar_evento(self, tipo_evento: str, data: dict, id_evento: str):
        """Reacciona a un evento de integración de los servicios participantes."""
        if self.estado in (EstadoSaga.COMPLETADA, EstadoSaga.COMPENSADA, EstadoSaga.FALLIDA):
            raise SagaTerminada(f"La saga ya terminó ({self.estado.value}); evento {tipo_evento} ignorado")

        self._log(TipoEntrada.EVENTO_RECIBIDO, paso=self.paso_actual,
                  servicio=self._servicio_de_evento(tipo_evento), mensaje=tipo_evento,
                  detalle=f"Evento {tipo_evento} recibido (id {id_evento[:8]}…)", payload=data)
        # datos que aportan los eventos al contexto de la saga
        for k in ("id_trabajo", "id_proveedor", "monto", "moneda", "pais", "id_pago"):
            if k in data and data[k] not in (None, ""):
                self.datos[k] = data[k]

        if self.estado == EstadoSaga.EN_CURSO:
            defn = self._definicion(self.paso_actual)
            if tipo_evento == defn["evento_ok"]:
                self.pasos_completados.append(defn["paso"].value)
                self._log(TipoEntrada.PASO_OK, paso=defn["paso"], servicio=defn["servicio"],
                          mensaje=tipo_evento, detalle=f"Paso {defn['paso'].value} completado")
                idx = DEFINICION.index(defn)
                if idx + 1 < len(DEFINICION):
                    self._enviar_paso(DEFINICION[idx + 1])
                else:
                    self._terminar(EstadoSaga.COMPLETADA, "Transacción larga completada: cotización aceptada, pago retenido, trabajo agendado")
            elif tipo_evento == defn["evento_fallo"]:
                self.motivo_fallo = data.get("motivo", tipo_evento)
                self._log(TipoEntrada.PASO_FALLIDO, paso=defn["paso"], servicio=defn["servicio"],
                          mensaje=tipo_evento, detalle=f"Paso {defn['paso'].value} FALLÓ: {self.motivo_fallo}")
                self._iniciar_compensacion()
            # otros eventos (p. ej. duplicados fuera de orden) solo quedan en el log

        elif self.estado == EstadoSaga.COMPENSANDO:
            defn = self._definicion(self.paso_actual)
            if tipo_evento == defn["evento_compensado"]:
                self._log(TipoEntrada.COMPENSACION_OK, paso=defn["paso"], servicio=defn["servicio"],
                          mensaje=tipo_evento, detalle=f"Compensación de {defn['paso'].value} confirmada")
                self.pasos_completados.remove(defn["paso"].value)
                self._compensar_siguiente()

    def _iniciar_compensacion(self):
        self.estado = EstadoSaga.COMPENSANDO
        self._compensar_siguiente()

    def _compensar_siguiente(self):
        """Compensa los pasos completados en ORDEN INVERSO."""
        pendientes = [p for p in reversed(self.pasos_completados)
                      if self._definicion(p)["compensacion"]]
        if not pendientes:
            self._terminar(EstadoSaga.COMPENSADA,
                           f"Compensación completa: el sistema volvió a un estado consistente. Motivo: {self.motivo_fallo}")
            return
        defn = self._definicion(pendientes[0])
        self.paso_actual = defn["paso"].value
        data = self._datos_para(defn["compensacion"])
        self.comandos_pendientes.append(ComandoPendiente(defn["compensacion"], defn["topico"], data, True))
        self._log(TipoEntrada.COMPENSACION_ENVIADA, paso=defn["paso"], servicio=defn["servicio"],
                  mensaje=defn["compensacion"],
                  detalle=f"Compensación {defn['compensacion']} → {defn['topico']}", payload=data)

    def _terminar(self, estado: EstadoSaga, detalle: str):
        self.estado = estado
        self.paso_actual = None
        self.fecha_fin = datetime.utcnow()
        self._log(TipoEntrada.FIN, servicio="saga", mensaje=estado.value, detalle=detalle,
                  payload={"pasos_completados": self.pasos_completados,
                           "duracion_ms": int((self.fecha_fin - self.fecha_inicio).total_seconds() * 1000)})

    @staticmethod
    def _servicio_de_evento(tipo_evento: str) -> str:
        if tipo_evento.startswith("Cotizacion"):
            return "cotizaciones"
        if tipo_evento.startswith("Pago"):
            return "pagos"
        if tipo_evento.startswith("Trabajo"):
            return "trabajos"
        return "?"

    def tomar_comandos_pendientes(self) -> list:
        pendientes, self.comandos_pendientes = self.comandos_pendientes, []
        return pendientes
