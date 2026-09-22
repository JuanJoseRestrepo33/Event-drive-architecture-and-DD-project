"""Reglas de negocio del dominio de trabajos."""
from trabajos.seedwork.dominio.reglas import ReglaNegocio


class DebeExistirPagoRetenido(ReglaNegocio):
    def __init__(self, id_pago, mensaje="No se agenda un trabajo sin pago retenido"):
        super().__init__(mensaje)
        self.id_pago = id_pago

    def es_valido(self) -> bool:
        return bool(self.id_pago)


class ProveedorDebeTenerDisponibilidad(ReglaNegocio):
    """Regla de negocio del núcleo: un trabajo solo se agenda si el proveedor
    tiene cupo. En la POC la disponibilidad se simula con una lista de
    proveedores sin cupo (env PROVEEDORES_SIN_CUPO, default PRV-SIN-CUPO)."""
    def __init__(self, id_proveedor, sin_cupo, mensaje="El proveedor no tiene disponibilidad para el trabajo"):
        super().__init__(mensaje)
        self.id_proveedor = id_proveedor
        self.sin_cupo = sin_cupo

    def es_valido(self) -> bool:
        return self.id_proveedor not in self.sin_cupo
