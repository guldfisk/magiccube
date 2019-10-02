from abc import abstractmethod

from mtgorp.models.serilization.serializeable import Serializeable, PersistentHashable

from mtgimg.interface import Imageable


class Lap(Serializeable, Imageable, PersistentHashable):

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
