from abc import abstractmethod

from mtgorp.models.serilization.serializeable import Serializeable, PersistentHashable, serialization_model

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
