"""Reglas de negocio del dominio de trabajos."""
from trabajos.seedwork.dominio.reglas import ReglaNegocio


class DebeExistirPagoRetenido(ReglaNegocio):
    def __init__(self, id_pago, mensaje="No se agenda un trabajo sin pago retenido"):
        super().__init__(mensaje)
        self.id_pago = id_pago

    def es_valido(self) -> bool:
        return bool(self.id_pago)
