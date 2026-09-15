"""Fábricas reusables parte del seedwork del proyecto"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .mixins import ValidarReglasMixin


@dataclass
class Fabrica(ABC, ValidarReglasMixin):
    @abstractmethod
    def crear_objeto(self, obj: any, mapeador: any = None) -> any:
        ...
