import typing as t

import hashlib
import itertools

from collections import OrderedDict

from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator
from mtgorp.models.persistent.printing import Printing
from mtgorp.utilities.containers import HashableMultiset
from mtgorp.tools.search.pattern import Pattern

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

		self._persistent_hash = None #type: str

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

	@staticmethod
	def _multiset_to_indented_string(ms: HashableMultiset[Printing]) -> str:
		return '\n'.join(
			f'\t{multiplicity}x {printing}'
			for printing, multiplicity in
			sorted(
				ms.items(),
				key = lambda item: str(item[0])
			)
		)

	@property
	def pp_string(self) -> str:
		return '\n'.join(
			f'{pickable_type}:\n{self._multiset_to_indented_string(pickables)}'
			for pickable_type, pickables in
			OrderedDict(
				printings = self._printings,
				traps = self._traps,
				tickets = self._tickets,
				purples = self._purples,
			).items()
		)

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

	def filter(self, pattern: Pattern[Printing]) -> 'Cube':
		return self.__class__(
			printings = pattern.matches(self._printings),
			traps = (
				trap
				for trap in
				self._traps
				if any(pattern.matches(trap))
			),
			tickets = (
				ticket
				for ticket in
				self._tickets
				if any(pattern.matches(ticket))
			),
			purples=self._purples,
		)

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
	
	def persistent_hash(self) -> str:
		if self._persistent_hash is not None:
			return self._persistent_hash

		hasher = hashlib.sha512()

		for printing in sorted(self._printings, key=lambda _printing: _printing.id):
			hasher.update(str(printing.id).encode('ASCII'))

		for persistent_hash in itertools.chain(
			sorted(
				trap.persistent_hash() for trap in self._traps
			),
			sorted(
				ticket.persistent_hash() for ticket in self._tickets
			),
			sorted(
				purple.persistent_hash() for purple in self._purples
			),
		):
			hasher.update(persistent_hash.encode('UTF-8'))

		self._persistent_hash = hasher.hexdigest()

		return self._persistent_hash

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
		return f'{self.__class__.__name__}({self.__hash__()})'

