from __future__ import annotations

import typing as t
from abc import abstractmethod

from mtgorp.models.persistent.printing import Printing
from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator

from magiccube.laps.lap import Lap


Cubeable = t.Union[Lap, Printing]


class CubeableCollection(Serializeable):

    @property
    @abstractmethod
    def cubeables(self) -> t.Iterable[Cubeable]:
        pass

    @abstractmethod
    def serialize(self) -> serialization_model:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CubeableCollection:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass