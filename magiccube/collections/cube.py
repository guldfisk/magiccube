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

	@property
	def all_printings(self) -> t.Iterator[Printing]:
		for printing in self._printings:
			yield printing
		for trap in self._traps:
			for printing in trap:
				yield printing
		for ticket in self._tickets:
			for printing in ticket:
				yield printing

	def __iter__(self) -> t.Iterator[Printing]:
		return self.all_printings

	def __len__(self) -> int:
		return len(self._printings) + len(self._traps) + len(self._tickets)

	def to_model_tree(self) -> model_tree:
		return {
			'printings': self._printings,
			'traps': (trap.to_model_tree() for trap in self._traps),
			'tickets': (ticket.to_model_tree() for ticket in self._tickets),
		}

	@classmethod
	def from_model_tree(cls, tree: model_tree) -> 'Cube':
		return cls(
			tree['printings'],
			(Trap.from_model_tree(trap) for trap in tree.get('traps', ())),
			(Ticket.from_model_tree(ticket) for ticket in tree.get('tickets', ())),
		)

	def __repr__(self) -> str:
		return f'{self.__class__.__name__}({len(self)})'

	def __hash__(self) -> int:
		return hash((self._printings, self._traps, self._tickets))

	def __eq__(self, other: object) -> bool:
		return (
			isinstance(other, self.__class__)
			and self._printings == other._printings
			and self._traps == other._traps
			and self._tickets == other._tickets
		)


