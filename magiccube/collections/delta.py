from __future__ import annotations

import itertools
import logging
import typing as t

from mtgorp.models.persistent.cardboard import Cardboard
from yeetlong.counters import FrozenCounter
from yeetlong.multiset import FrozenMultiset

from mtgorp.models.persistent.printing import Printing
from mtgorp.models.serilization.serializeable import serialization_model, Inflator, PersistentHashable

from magiccube.collections.cube import Cube, Cubeable
from magiccube.collections.cubeable import CubeableCollection, BaseCubeable
from magiccube.laps.lap import Lap
from magiccube.laps.purples.purple import Purple
from magiccube.laps.tickets.ticket import Ticket
from magiccube.laps.traps.trap import Trap


class CubeDelta(object):

    def __init__(self, original: Cube, current: Cube):
        logging.warn(f'{self.__class__.__name__} is deprecated')

        self._original = original
        self._current = current

        self._new_cubeables = None
        self._removed_cubeables = None
        self._new_printings = None
        self._removed_printings = None

    @property
    def new_cubeables(self) -> Cube:
        if self._new_cubeables is None:
            self._new_cubeables = self._current - self._original

        return self._new_cubeables

    @property
    def removed_cubeables(self) -> Cube:
        if self._removed_cubeables is None:
            self._removed_cubeables = self._original - self._current

        return self._removed_cubeables

    @property
    def new_printings(self) -> FrozenMultiset[Printing]:
        if self._new_printings is None:
            self._new_printings = (
                FrozenMultiset(self._current.all_printings)
                - FrozenMultiset(self._original.all_printings)
            )

        return self._new_printings

    @property
    def new_cardboards(self) -> FrozenMultiset[Cardboard]:
        return FrozenMultiset(printing.cardboard for printing in self.new_printings)

    @property
    def removed_printings(self) -> FrozenMultiset[Printing]:
        if self._removed_printings is None:
            self._removed_printings = (
                FrozenMultiset(self._original.all_printings)
                - FrozenMultiset(self._current.all_printings)
            )

        return self._removed_printings

    @property
    def removed_cardboards(self) -> FrozenMultiset[Cardboard]:
        return FrozenMultiset(printing.cardboard for printing in self.removed_printings)

    @staticmethod
    def _multiset_to_indented_string(ms: FrozenMultiset[t.Union[Cardboard, Printing]]) -> str:
        return '\n'.join(
            f'\t{multiplicity}x {printing}'
            for printing, multiplicity in
            sorted(
                ms.items(),
                key = lambda item: str(item[0])
            )
        )

    @property
    def report(self) -> str:
        return f'New cubeables ({len(self.new_cubeables)}):\n{self.new_cubeables.pp_string}\n------\n' \
               f'Removed cubeables ({len(self.removed_cubeables)}):\n{self.removed_cubeables.pp_string}\n------\n' \
               f'New cardboards ({len(self.new_cardboards)}):\n' \
               f'{self._multiset_to_indented_string(self.new_cardboards)}\n' \
               f'Removed cardboards ({len(self.removed_cardboards)}):\n' \
               f'{self._multiset_to_indented_string(self.removed_cardboards)}'

    def as_operation(self) -> CubeDeltaOperation:
        return CubeDeltaOperation(
            self._current.cubeables.elements()
        ) - CubeDeltaOperation(
            self._original.cubeables.elements()
        )


class CubeDeltaOperation(CubeableCollection, PersistentHashable):

    def __init__(
        self,
        cubeables: t.Optional[t.Mapping[Cubeable, int]] = None,
    ):
        self._cubeables: FrozenCounter[Cubeable] = (
            FrozenCounter()
            if cubeables is None else
            FrozenCounter(cubeables)
        )

    @property
    def items(self) -> t.Iterable[BaseCubeable]:
        return self._cubeables

    @property
    def printings(self) -> t.Iterator[t.Tuple[Printing, int]]:
        return (
            (cubeable, multiplicity)
            for cubeable, multiplicity in
            self._cubeables.items()
            if isinstance(cubeable, Printing)
        )

    @property
    def new_printings(self) -> t.Iterator[t.Tuple[Printing, int]]:
        return (
            (
                (cubeable, multiplicity)
                for cubeable, multiplicity in
                self.printings
                if multiplicity > 0
            )
        )

    @property
    def removed_printings(self) -> t.Iterator[t.Tuple[Printing, int]]:
        return (
            (
                (cubeable, -multiplicity)
                for cubeable, multiplicity in
                self.printings
                if multiplicity < 0
            )
        )

    @property
    def traps(self) -> t.Iterator[t.Tuple[Trap, int]]:
        return (
            (cubeable, multiplicity)
            for cubeable, multiplicity in
            self._cubeables.items()
            if isinstance(cubeable, Trap)
        )

    @property
    def new_traps(self) -> t.Iterator[t.Tuple[Trap, int]]:
        return (
            (
                (trap, multiplicity)
                for trap, multiplicity in
                self.traps
                if multiplicity > 0
            )
        )

    @property
    def removed_traps(self) -> t.Iterator[t.Tuple[Trap, int]]:
        return (
            (
                (trap, -multiplicity)
                for trap, multiplicity in
                self.traps
                if multiplicity < 0
            )
        )

    @property
    def tickets(self) -> t.Iterator[t.Tuple[Ticket, int]]:
        return (
            (cubeable, multiplicity)
            for cubeable, multiplicity in
            self._cubeables.items()
            if isinstance(cubeable, Ticket)
        )

    @property
    def new_tickets(self) -> t.Iterator[t.Tuple[Ticket, int]]:
        return (
            (
                (ticket, multiplicity)
                for ticket, multiplicity in
                self.tickets
                if multiplicity > 0
            )
        )

    @property
    def removed_tickets(self) -> t.Iterator[t.Tuple[Ticket, int]]:
        return (
            (
                (ticket, -multiplicity)
                for ticket, multiplicity in
                self.tickets
                if multiplicity < 0
            )
        )

    @property
    def purples(self) -> t.Iterator[t.Tuple[Purple, int]]:
        return (
            (cubeable, multiplicity)
            for cubeable, multiplicity in
            self._cubeables.items()
            if isinstance(cubeable, Purple)
        )

    @property
    def new_purples(self) -> t.Iterator[t.Tuple[Purple, int]]:
        return (
            (
                (purple, multiplicity)
                for purple, multiplicity in
                self.purples
                if multiplicity > 0
            )
        )

    @property
    def removed_purples(self) -> t.Iterator[t.Tuple[Purple, int]]:
        return (
            (
                (purple, -multiplicity)
                for purple, multiplicity in
                self.purples
                if multiplicity < 0
            )
        )

    @property
    def laps(self) -> t.Iterator[t.Tuple[Lap, int]]:
        return (
            (cubeable, multiplicity)
            for cubeable, multiplicity in
            self._cubeables.items()
            if isinstance(cubeable, Lap)
        )

    @property
    def cubeables(self) -> FrozenCounter[Cubeable]:
        return self._cubeables

    @property
    def new_cubeables(self) -> t.Iterator[t.Tuple[Cubeable, int]]:
        return (
            (cubeable, multiplicity)
            for cubeable, multiplicity in
            self._cubeables.items()
            if multiplicity > 0
        )

    @property
    def removed_cubeables(self) -> t.Iterator[t.Tuple[Cubeable, int]]:
        return (
            (cubeable, multiplicity)
            for cubeable, multiplicity in
            self._cubeables.items()
            if multiplicity < 0
        )

    @property
    def all_removed_printings(self) -> t.Iterable[Printing]:
        for printing, multiplicity in self.removed_printings:
            yield from itertools.repeat(printing, multiplicity)
        for trap, multiplicity in self.removed_traps:
            for _ in range(multiplicity):
                yield from trap
        for ticket, multiplicity in self.removed_tickets:
            for _ in range(multiplicity):
                yield from ticket.options

    @property
    def all_new_printings(self) -> t.Iterable[Printing]:
        for printing, multiplicity in self.new_printings:
            yield from itertools.repeat(printing, multiplicity)
        for trap, multiplicity in self.new_traps:
            for _ in range(multiplicity):
                yield from trap
        for ticket, multiplicity in self.new_tickets:
            for _ in range(multiplicity):
                yield from ticket.options

    def serialize(self) -> serialization_model:
        return {
            'printings': self.printings,
            'traps': self.traps,
            'tickets': self.tickets,
            'purples': self.purples,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CubeDeltaOperation:
        return cls(
            {
                cubeable: multiplicity
                for cubeable, multiplicity in
                itertools.chain(
                    (
                        (inflator.inflate(Printing, printing), multiplicity)
                        for printing, multiplicity in
                        value.get('printings', [])
                    ),
                    (
                        (Trap.deserialize(trap, inflator), multiplicity)
                        for trap, multiplicity in
                        value.get('traps', [])
                    ),
                    (
                        (Ticket.deserialize(ticket, inflator), multiplicity)
                        for ticket, multiplicity in
                        value.get('tickets', [])
                    ),
                    (
                        (Purple.deserialize(purple, inflator), multiplicity)
                        for purple, multiplicity in
                        value.get('purples', [])
                    )
                )
            }
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        for printing, multiplicity in sorted(self.printings, key = lambda pair: pair[0].id):
            yield str(printing.id).encode('ASCII')
            yield str(multiplicity).encode('ASCII')
        for persistent_hash, multiplicity in sorted(
            (
                (lap.persistent_hash(), multiplicity)
                for lap, multiplicity in
                self.laps
            ),
            key = lambda pair: pair[0],
        ):
            yield persistent_hash.encode('ASCII')
            yield str(multiplicity).encode('ASCII')

    def __add__(self, other: t.Union[CubeDeltaOperation, Cube]) -> CubeDeltaOperation:
        return self.__class__(
            self._cubeables + other.cubeables
        )

    __radd__ = __add__

    def __sub__(self, other: t.Union[CubeDeltaOperation, Cube]) -> CubeDeltaOperation:
        return self.__class__(
            self._cubeables - other.cubeables
        )

    __rsub__ = __sub__

    def __mul__(self, other: int) -> CubeDeltaOperation:
        return self.__class__(
            self._cubeables * other
        )

    __rmul__ = __mul__

    def __invert__(self):
        return self.__class__(
            self._cubeables * -1
        )

    def __hash__(self) -> int:
        return hash(self._cubeables)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._cubeables == other._cubeables
        )

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            self._cubeables,
        )
