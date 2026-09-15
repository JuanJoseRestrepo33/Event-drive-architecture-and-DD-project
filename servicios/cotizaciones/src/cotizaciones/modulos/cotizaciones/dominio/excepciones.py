from cotizaciones.seedwork.dominio.excepciones import ExcepcionFabrica, ExcepcionDominio


class TipoObjetoNoExisteEnDominioCotizacionesExcepcion(ExcepcionFabrica):
    def __init__(self, mensaje='No existe una fábrica para el tipo solicitado en el módulo de cotizaciones'):
        self.__mensaje = mensaje

    def __str__(self):
        return str(self.__mensaje)


class CotizacionNoExiste(ExcepcionDominio):
    def __init__(self, id_cotizacion):
        self.__mensaje = f'La cotización {id_cotizacion} no existe'

    def __str__(self):
        return str(self.__mensaje)
