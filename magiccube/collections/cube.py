import typing as t

from lazy_property import LazyProperty

from mtgorp.models.collections.serilization.serializeable import Serializeable, model_tree
from mtgorp.models.persistent.printing import Printing
from mtgorp.utilities.containers import HashableMultiset

from magiccube.laps.lap import Lap
from magiccube.laps.traps.trap import Trap
from magiccube.laps.tickets.ticket import Ticket


cubeable = t.Union[Lap, Printing]


class Cube(Serializeable):

	def __init__(
		self,
		printings: t.Iterable[Printing],
		traps: t.Optional[t.Iterable[Trap]] = None,
		tickets: t.Optional[t.Iterable[Ticket]] = None,
	):
		self._printings = HashableMultiset(printings)
		self._traps = HashableMultiset() if traps is None else HashableMultiset(traps)
		self._tickets = HashableMultiset() if tickets is None else HashableMultiset(tickets)

	@property
	def printings(self) -> HashableMultiset[Printing]:
		return self._printings

	@property
	def traps(self) -> HashableMultiset[Trap]:
		return self._traps

	@property
	def tickets(self) -> HashableMultiset[Ticket]:
		return self._tickets

	@LazyProperty
	def cubeables(self) -> HashableMultiset[cubeable]:
		return self._printings + self._traps + self._tickets

	def to_model_tree(self) -> model_tree:
		return {
			'printings': self._printings,
			'traps': self._traps,
			'tickets': self._tickets,
		}

	@classmethod
	def from_model_tree(cls, tree: model_tree) -> 'Cube':
		return cls(
			tree['printings'],
			tree.get('traps', ()),
			tree.get('tickets', ()),
		)

