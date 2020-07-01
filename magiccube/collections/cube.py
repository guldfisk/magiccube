from __future__ import annotations

import typing as t
import itertools

from collections import OrderedDict

from yeetlong.multiset import FrozenMultiset

from mtgorp.models.serilization.serializeable import serialization_model, Inflator, PersistentHashable
from mtgorp.models.persistent.printing import Printing
from mtgorp.tools.search.pattern import Pattern

from magiccube.laps.lap import Lap
from magiccube.laps.traps.trap import Trap
from magiccube.laps.tickets.ticket import Ticket
from magiccube.laps.purples.purple import Purple
from magiccube.collections.cubeable import Cubeable, CubeableCollection


class Cube(CubeableCollection, PersistentHashable):

    def __init__(
        self,
        cubeables: t.Union[t.Iterable[Cubeable], t.Mapping[Cubeable, int], None] = None,
    ):
        self._cubeables = FrozenMultiset() if cubeables is None else FrozenMultiset(cubeables)

        self._printings: t.Optional[FrozenMultiset[Printing]] = None
        self._traps: t.Optional[FrozenMultiset[Trap]] = None
        self._garbage_traps: t.Optional[FrozenMultiset[Trap]] = None
        self._tickets: t.Optional[FrozenMultiset[Ticket]] = None
        self._purples: t.Optional[FrozenMultiset[Purple]] = None
        self._laps: t.Optional[FrozenMultiset[Lap]] = None

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
    def garbage_traps(self) -> FrozenMultiset[Trap]:
        if self._garbage_traps is None:
            self._garbage_traps = FrozenMultiset(
                cubeable
                for cubeable in
                self._cubeables
                if isinstance(cubeable, Trap)
                and cubeable.intention_type == Trap.IntentionType.GARBAGE
            )
        return self._garbage_traps

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
            (
                ('printings', self.printings),
                ('traps', self.traps),
                ('tickets', self.tickets),
                ('purples', self.purples)
            )
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
                ) or (
                    isinstance(cubeable, t.Iterable)
                    and any(pattern.matches(cubeable))
                )
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

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        for printing in sorted(self.printings, key=lambda _printing: _printing.id):
            yield str(printing.id).encode('ASCII')
        for persistent_hash in sorted(
            lap.persistent_hash()
            for lap in
            self.laps
        ):
            yield persistent_hash.encode('ASCII')

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._cubeables == other._cubeables
        )

    def __add__(self, other: t.Union[CubeableCollection, t.Iterable[Cubeable]]) -> Cube:
        if isinstance(other, CubeableCollection):
            return self.__class__(
                self._cubeables + other.cubeables
            )
        return self.__class__(
            self._cubeables + other
        )

    def __sub__(self, other: t.Union[CubeableCollection, t.Iterable[Cubeable]]) -> Cube:
        if isinstance(other, CubeableCollection):
            return self.__class__(
                self._cubeables - other.cubeables
            )
        return self.__class__(
            self._cubeables - other
        )
    
    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.__hash__()})'

