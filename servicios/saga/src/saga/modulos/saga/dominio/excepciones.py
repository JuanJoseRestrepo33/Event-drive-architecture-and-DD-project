from saga.seedwork.dominio.excepciones import ExcepcionDominio


class SagaNoExiste(ExcepcionDominio):
    def __init__(self, ref):
        self.__mensaje = f"No existe una saga para {ref}"

    def __str__(self):
        return self.__mensaje
