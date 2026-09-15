from trabajos.seedwork.dominio.excepciones import ExcepcionFabrica


class TipoObjetoNoExisteEnDominioTrabajosExcepcion(ExcepcionFabrica):
    def __init__(self, mensaje='No existe una fábrica para el tipo solicitado en el módulo de trabajos'):
        self.__mensaje = mensaje

    def __str__(self):
        return str(self.__mensaje)
