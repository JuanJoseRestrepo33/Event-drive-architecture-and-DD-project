"""Interfaces (puertos) para los repositorios y mapeadores del dominio"""
from abc import ABC, abstractmethod
from uuid import UUID


class Repositorio(ABC):
    @abstractmethod
    def obtener_por_id(self, id: UUID):
        ...

    @abstractmethod
    def obtener_todos(self) -> list:
        ...

    @abstractmethod
    def agregar(self, entity):
        ...

    @abstractmethod
    def actualizar(self, entity):
        ...

    @abstractmethod
    def eliminar(self, entity_id: UUID):
        ...


class Mapeador(ABC):
    @abstractmethod
    def obtener_tipo(self) -> type:
        ...

    @abstractmethod
    def entidad_a_dto(self, entidad):
        ...

    @abstractmethod
    def dto_a_entidad(self, dto):
        ...
