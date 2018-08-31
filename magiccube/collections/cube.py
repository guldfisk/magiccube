import typing as t

from lazy_property import LazyProperty

from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator
from mtgorp.models.persistent.printing import Printing
from mtgorp.utilities.containers import HashableMultiset

from magiccube.laps.lap import Lap
from magiccube.laps.traps.trap import Trap
from magiccube.laps.tickets.ticket import Ticket


cubeable = t.Union[Lap, Printing]


class Cube(Serializeable):

	def __init__(
		self,
		printings: t.Optional[t.Iterable[Printing]] = None,
		traps: t.Optional[t.Iterable[Trap]] = None,
		tickets: t.Optional[t.Iterable[Ticket]] = None,
	):
		self._printings = HashableMultiset() if printings is None else HashableMultiset(printings)
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
		for printing in self.garbage_printings:
			yield printing

	@property
	def garbage_printings(self) -> t.Iterator[Printing]:
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

	def serialize(self) -> serialization_model:
		return {
			'printings': self._printings,
			'traps': self._traps,
			'tickets': self._tickets,
		}

	@classmethod
	def deserialize(cls, value: serialization_model, inflator: Inflator) -> 'Cube':
		return cls(
			inflator.inflate_all(Printing, value['printings']),
			(
				Trap.deserialize(trap, inflator)
				for trap in
				value.get('traps', ())
			),
			(
				Ticket.deserialize(ticket, inflator)
				for ticket in
				value.get('tickets', ())
			),
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

	def __add__(self, other):
		return self.__class__(
			self._printings + other.printings,
			self._traps + other.traps,
			self._tickets + other.tickets,
		)

	def __sub__(self, other):
		return self.__class__(
			self._printings - other.printings,
			self._traps - other.traps,
			self._tickets - other.tickets,
		)

	def __str__(self) -> str:
		return f'{self.__class__.__name__}({self.printings}, {self.traps}, {self.tickets})'

