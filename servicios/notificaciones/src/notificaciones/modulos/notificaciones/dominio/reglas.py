"""Reglas de negocio del dominio de notificaciones."""
from notificaciones.seedwork.dominio.reglas import ReglaNegocio


class DestinatarioObligatorio(ReglaNegocio):
    def __init__(self, destinatario, mensaje="Una notificación requiere destinatario"):
        super().__init__(mensaje)
        self.destinatario = destinatario

    def es_valido(self) -> bool:
        return bool(self.destinatario)
