from __future__ import annotations

import typing as t

from abc import abstractmethod

from mtgorp.models.serilization.serializeable import Serializeable, PersistentHashable, serialization_model, Inflator

from mtgimg.interface import Imageable


class Lap(Serializeable, Imageable, PersistentHashable):

    def serialize(self) -> serialization_model:
        return {'type': self.__class__.__name__}

    @property
    def id(self):
        return self.persistent_hash()

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass


class CardboardLap(Serializeable, PersistentHashable):

    def serialize(self) -> serialization_model:
        return {'type': self.__class__.__name__}

    @classmethod
    @abstractmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CardboardLap:
        pass

    def __hash__(self) -> int:
        pass

    def __eq__(self, other: object) -> bool:
        pass

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        pass