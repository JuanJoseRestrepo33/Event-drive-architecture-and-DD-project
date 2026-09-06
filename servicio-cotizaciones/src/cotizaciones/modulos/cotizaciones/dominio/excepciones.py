"""Excepciones del dominio de cotizaciones"""
from cotizaciones.seedwork.dominio.excepciones import ExcepcionFabrica, ExcepcionDominio


class TipoObjetoNoExisteEnDominioCotizacionesExcepcion(ExcepcionFabrica):
    def __init__(self, mensaje='No existe una fábrica para el tipo solicitado en el módulo de cotizaciones'):
        super().__init__(mensaje)


class CotizacionNoExiste(ExcepcionDominio):
    ...
