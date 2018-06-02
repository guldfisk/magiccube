
from abc import abstractmethod

from mtgorp.models.collections.serilization.serializeable import Serializeable

from mtgimg.interface import Imageable


class Lap(Serializeable, Imageable):

	@abstractmethod
	def __hash__(self) -> int:
		pass

	@abstractmethod
	def __eq__(self, other: object) -> bool:
		pass
