import typing as t

from lazy_property import LazyProperty

from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator
from mtgorp.models.persistent.printing import Printing
from mtgorp.utilities.containers import HashableMultiset

from magiccube.laps.lap import Lap
from magiccube.laps.traps.trap import Trap
from magiccube.laps.tickets.ticket import Ticket
from magiccube.laps.purples.purple import Purple


cubeable = t.Union[Lap, Printing]


class Cube(Serializeable):

	def __init__(
		self,
		printings: t.Optional[t.Iterable[Printing]] = None,
		traps: t.Optional[t.Iterable[Trap]] = None,
		tickets: t.Optional[t.Iterable[Ticket]] = None,
		purples: t.Optional[t.Iterable[Purple]] = None,
	):
		self._printings = HashableMultiset() if printings is None else HashableMultiset(printings)
		self._traps = HashableMultiset() if traps is None else HashableMultiset(traps)
		self._tickets = HashableMultiset() if tickets is None else HashableMultiset(tickets)
		self._purples = HashableMultiset() if purples is None else HashableMultiset(purples)

		self._laps = None #type: HashableMultiset[Lap]
		self._cubeables = None #type: HashableMultiset[cubeable]

	@property
	def printings(self) -> HashableMultiset[Printing]:
		return self._printings

	@property
	def traps(self) -> HashableMultiset[Trap]:
		return self._traps

	@property
	def tickets(self) -> HashableMultiset[Ticket]:
		return self._tickets

	@property
	def purples(self) -> HashableMultiset[Purple]:
		return self._purples

	@property
	def laps(self) -> HashableMultiset[Lap]:
		if self._laps is None:
			self._laps = self._traps + self._tickets + self._purples

		return self._laps

	@property
	def cubeables(self) -> HashableMultiset[cubeable]:
		if self._cubeables is None:
			self._cubeables = self._printings + self.laps

		return self._cubeables

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
		return len(self._printings) + len(self._traps) + len(self._tickets) + len(self._purples)

	def serialize(self) -> serialization_model:
		return {
			'printings': self._printings,
			'traps': self._traps,
			'tickets': self._tickets,
			'purples': self._purples,
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
			(
				Purple.deserialize(purple, inflator)
				for purple in
				value.get('purples', ())
			),
		)

	def __repr__(self) -> str:
		return f'{self.__class__.__name__}({len(self)})'

	def __hash__(self) -> int:
		return hash((self._printings, self._traps, self._tickets, self._purples))

	def __eq__(self, other: object) -> bool:
		return (
			isinstance(other, self.__class__)
			and self._printings == other._printings
			and self._traps == other._traps
			and self._tickets == other._tickets
			and self._purples == other._purples
		)

	def __add__(self, other):
		return self.__class__(
			self._printings + other.printings,
			self._traps + other.traps,
			self._tickets + other.tickets,
			self._purples + other.purples,
		)

	def __sub__(self, other):
		return self.__class__(
			self._printings - other.printings,
			self._traps - other.traps,
			self._tickets - other.tickets,
			self._purples - other.purples,
		)

	def __str__(self) -> str:
		return f'{self.__class__.__name__}({self.printings}, {self.traps}, {self.tickets}, {self.purples})'

