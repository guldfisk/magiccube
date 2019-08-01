from __future__ import annotations

import typing as t

import itertools

from yeetlong.multiset import FrozenMultiset
from yeetlong.counters import FrozenCounter

from mtgorp.models.persistent.printing import Printing
from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator

from magiccube.collections.cube import Cube, Cubeable
from magiccube.laps.lap import Lap
from magiccube.laps.purples.purple import Purple
from magiccube.laps.tickets.ticket import Ticket
from magiccube.laps.traps.trap import Trap


class CubeDelta(object):
    
    def __init__(self, original: Cube, current: Cube):
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
    def removed_printings(self) -> FrozenMultiset[Printing]:
        if self._removed_printings is None:
            self._removed_printings = (
                FrozenMultiset(self._original.all_printings)
                - FrozenMultiset(self._current.all_printings)
            )

        return self._removed_printings

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
    def report(self) -> str:
        return f'New cubeables ({len(self.new_cubeables)}):\n{self.new_cubeables.pp_string}\n------\n' \
               f'Removed cubeables ({len(self.removed_cubeables)}):\n{self.removed_cubeables.pp_string}\n------\n' \
               f'New printings ({len(self.new_printings)}):\n' \
               f'{self._multiset_to_indented_string(self.new_printings)}\n' \
               f'Removed printings ({len(self.removed_printings)}):\n' \
               f'{self._multiset_to_indented_string(self.removed_printings)}'

    def as_operation(self) -> CubeDeltaOperation:
        return CubeDeltaOperation(
            self._current.cubeables.elements()
        ) - CubeDeltaOperation(
            self._original.cubeables.elements()
        )


class CubeDeltaOperation(Serializeable):

    def __init__(
        self,
        cubeables: t.Optional[t.Mapping[Cubeable, int]] = None,
    ):
        self._cubeables = (
            FrozenCounter()
            if cubeables is None else
            FrozenCounter(cubeables)
        ) #type: FrozenCounter[Cubeable]

    @property
    def printings(self) -> t.Iterator[t.Tuple[Printing, int]]:
        return (
            (cubeable, multiplicity)
            for cubeable, multiplicity in
            self._cubeables.items()
            if isinstance(cubeable, Printing)
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
    def tickets(self) -> t.Iterator[t.Tuple[Ticket, int]]:
        return (
            (cubeable, multiplicity)
            for cubeable, multiplicity in
            self._cubeables.items()
            if isinstance(cubeable, Ticket)
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
    def laps(self) -> t.Iterator[t.Tuple[Lap, int]]:
        return itertools.chain(
            self.traps,
            self.tickets,
            self.purples,
        )

    @property
    def cubeables(self) -> FrozenCounter[Cubeable]:
        return self._cubeables

    def serialize(self) -> serialization_model:
        return {
            'printings': self.printings,
            'traps': self.traps,
            'tickets': self.tickets,
            'purples': self.purples,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> 'Serializeable':
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