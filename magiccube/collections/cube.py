from __future__ import annotations

import typing as t

import hashlib
import itertools
from collections import OrderedDict

from yeetlong.multiset import FrozenMultiset

from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator
from mtgorp.models.persistent.printing import Printing
from mtgorp.tools.search.pattern import Pattern

from magiccube.laps.lap import Lap
from magiccube.laps.traps.trap import Trap
from magiccube.laps.tickets.ticket import Ticket
from magiccube.laps.purples.purple import Purple


Cubeable = t.Union[Lap, Printing]


class Cube(Serializeable):

    def __init__(
        self,
        cubeables: t.Optional[t.Iterable[Cubeable]] = None,
    ):
        self._cubeables = FrozenMultiset() if cubeables is None else FrozenMultiset(cubeables)

        self._printings = None #type: FrozenMultiset[Printing]
        self._traps = None #type: FrozenMultiset[Trap]
        self._tickets = None #type: FrozenMultiset[Ticket]
        self._purples = None #type: FrozenMultiset[Purple]
        self._laps = None #type: FrozenMultiset[Lap]
        self._persistent_hash = None #type: str

    @property
    def cubeables(self) -> FrozenMultiset[Cubeable]:
        return self._cubeables

    @property
    def printings(self) -> FrozenMultiset[Printing]:
        if self._printings is None:
            self._printings = FrozenMultiset(
                cubeable
                for cubeable in
                self._cubeables
                if isinstance(cubeable, Printing)
            )
        return self._printings

    @property
    def traps(self) -> FrozenMultiset[Trap]:
        if self._traps is None:
            self._traps = FrozenMultiset(
                cubeable
                for cubeable in
                self._cubeables
                if isinstance(cubeable, Trap)
            )
        return self._traps

    @property
    def tickets(self) -> FrozenMultiset[Ticket]:
        if self._tickets is None:
            self._tickets = FrozenMultiset(
                cubeable
                for cubeable in
                self._cubeables
                if isinstance(cubeable, Ticket)
            )
        return self._tickets

    @property
    def purples(self) -> FrozenMultiset[Purple]:
        if self._purples is None:
            self._purples = FrozenMultiset(
                cubeable
                for cubeable in
                self._cubeables
                if isinstance(cubeable, Purple)
            )
        return self._purples

    @staticmethod
    def _multiset_to_indented_string(ms: FrozenMultiset[Printing]) -> str:
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
                printings = self.printings,
                traps = self.traps,
                tickets = self.tickets,
                purples = self.purples,
            ).items()
        )

    @property
    def laps(self) -> FrozenMultiset[Lap]:
        if self._laps is None:
            self._laps = FrozenMultiset(
                cubeable
                for cubeable in
                self._cubeables
                if isinstance(cubeable, Lap)
            )
        return self._laps

    @property
    def all_printings(self) -> t.Iterator[Printing]:
        for printing in self.printings:
            yield printing
        yield from self.garbage_printings

    @property
    def garbage_printings(self) -> t.Iterator[Printing]:
        for trap in self.traps:
            yield from trap
        for ticket in self.tickets:
            yield from ticket

    def filter(self, pattern: Pattern[Printing]) -> Cube:
        return self.__class__(
            cubeables = (
                cubeable
                for cubeable in
                self._cubeables
                if (
                    isinstance(cubeable, Printing)
                    and pattern.match(cubeable)
                ) or any(pattern.matches(cubeable))
            ),
        )

    def __iter__(self) -> t.Iterator[Cubeable]:
        return self._cubeables.__iter__()

    def __len__(self) -> int:
        return len(self._cubeables)

    def serialize(self) -> serialization_model:
        return {
            'printings': self.printings,
            'traps': self.traps,
            'tickets': self.tickets,
            'purples': self.purples,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> Cube:
        return cls(
            cubeables = itertools.chain(
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
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({len(self)})'

    def __hash__(self) -> int:
        return hash(self._cubeables)
    
    def persistent_hash(self) -> str:
        if self._persistent_hash is not None:
            return self._persistent_hash

        hasher = hashlib.sha512()

        for printing in sorted(self.printings, key=lambda _printing: _printing.id):
            hasher.update(str(printing.id).encode('ASCII'))

        for persistent_hash in sorted(
            lap.persistent_hash()
            for lap in
            self.laps
        ):
            hasher.update(persistent_hash.encode('UTF-8'))

        self._persistent_hash = hasher.hexdigest()

        return self._persistent_hash

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._cubeables == other._cubeables
        )

    def __add__(self, other):
        return self.__class__(
            self._cubeables + other.cubeables
        )

    def __sub__(self, other):
        return self.__class__(
            self._cubeables - self._cubeables
        )

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.__hash__()})'

