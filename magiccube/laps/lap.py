from __future__ import annotations

from abc import abstractmethod

from mtgorp.models.serilization.serializeable import Serializeable, PersistentHashable, serialization_model

from mtgimg.interface import Imageable


class BaseLap(Serializeable, PersistentHashable):

    def serialize(self) -> serialization_model:
        return {'type': self.__class__.__name__}

    @property
    def id(self) -> str:
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


class Lap(BaseLap, Imageable):

    @property
    @abstractmethod
    def as_cardboards(self) -> CardboardLap:
        pass


class CardboardLap(BaseLap):
    pass
