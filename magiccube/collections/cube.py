from __future__ import annotations

import typing as t
import itertools
from abc import abstractmethod
from collections import OrderedDict

from numpy.random import choice

from yeetlong.multiset import FrozenMultiset, Multiset

from orp.models import OrpBase

from mtgorp.models.serilization.serializeable import serialization_model, Inflator, PersistentHashable
from mtgorp.models.interfaces import Printing, Cardboard
from mtgorp.tools.search.pattern import Pattern

from magiccube.laps.lap import Lap, BaseLap, CardboardLap
from magiccube.laps.traps.trap import Trap, BaseTrap, IntentionType, CardboardTrap
from magiccube.laps.tickets.ticket import Ticket, BaseTicket, CardboardTicket
from magiccube.laps.purples.purple import Purple, BasePurple, CardboardPurple
from magiccube.collections.cubeable import (
    Cubeable, CubeableCollection, BaseCubeableCollection, BaseCubeable,
    CardboardCubeable, CardboardCubeableCollection, cardboardize,
)


C = t.TypeVar('C', bound = BaseCubeable)
M = t.TypeVar('M', bound = OrpBase)
T = t.TypeVar('T', bound = BaseTrap)
I = t.TypeVar('I', bound = BaseTicket)
P = t.TypeVar('P', bound = BasePurple)
L = t.TypeVar('L', bound = BaseLap)


class BaseCube(BaseCubeableCollection, PersistentHashable, t.Generic[C, M, T, I, P, L]):

    def __init__(
        self,
        cubeables: t.Union[t.Iterable[C], t.Iterable[t.Tuple[C, int]], t.Mapping[C, int], None] = None,
    ):
        self._cubeables = FrozenMultiset() if cubeables is None else FrozenMultiset(cubeables)

        self._models: t.Optional[FrozenMultiset[M]] = None
        self._traps: t.Optional[FrozenMultiset[T]] = None
        self._garbage_traps: t.Optional[FrozenMultiset[T]] = None
        self._tickets: t.Optional[FrozenMultiset[I]] = None
        self._purples: t.Optional[FrozenMultiset[P]] = None
        self._laps: t.Optional[FrozenMultiset[L]] = None

    @property
    def items(self) -> t.Iterable[C]:
        return self._cubeables

    @property
    def models(self) -> FrozenMultiset[M]:
        if self._models is None:
            self._models = FrozenMultiset(
                cubeable
                    for cubeable in
                    self._cubeables
                    if isinstance(cubeable, OrpBase)
            )
        return self._models

    @property
    def cubeables(self) -> FrozenMultiset[C]:
        return self._cubeables

    @property
    def traps(self) -> FrozenMultiset[T]:
        if self._traps is None:
            self._traps = FrozenMultiset(
                cubeable
                    for cubeable in
                    self._cubeables
                    if isinstance(cubeable, BaseTrap)
            )
        return self._traps

    @property
    def garbage_traps(self) -> FrozenMultiset[T]:
        if self._garbage_traps is None:
            self._garbage_traps = FrozenMultiset(
                cubeable
                    for cubeable in
                    self._cubeables
                    if isinstance(cubeable, BaseTrap)
                       and cubeable.intention_type == IntentionType.GARBAGE
            )
        return self._garbage_traps

    @property
    def tickets(self) -> FrozenMultiset[I]:
        if self._tickets is None:
            self._tickets = FrozenMultiset(
                cubeable
                    for cubeable in
                    self._cubeables
                    if isinstance(cubeable, BaseTicket)
            )
        return self._tickets

    @property
    def purples(self) -> FrozenMultiset[P]:
        if self._purples is None:
            self._purples = FrozenMultiset(
                cubeable
                    for cubeable in
                    self._cubeables
                    if isinstance(cubeable, BasePurple)
            )
        return self._purples

    @property
    def laps(self) -> FrozenMultiset[L]:
        if self._laps is None:
            self._laps = FrozenMultiset(
                cubeable
                    for cubeable in
                    self._cubeables
                    if isinstance(cubeable, BaseLap)
            )
        return self._laps

    @property
    def all_models(self) -> t.Iterator[M]:
        for model in self.models:
            yield model
        yield from self.garbage_models

    @property
    def garbage_models(self) -> t.Iterator[M]:
        for trap in self.traps:
            yield from trap
        for ticket in self.tickets:
            yield from ticket

    def filter(self: B, pattern: Pattern[M]) -> B:
        return self.__class__(
            cubeables = (
                cubeable
                for cubeable in
                self._cubeables
                if (
                       isinstance(cubeable, OrpBase)
                       and pattern.match(cubeable)
                   ) or (
                       isinstance(cubeable, t.Iterable)
                       and any(pattern.matches(cubeable))
                   )
            ),
        )

    def scale(self, amount: int) -> BaseCube:
        current_size = len(self)

        if not current_size:
            raise ValueError('cannot scale empty cube')

        remaining = amount - current_size
        if remaining <= 0:
            return self
        factor = (amount / current_size) - 1
        additionals: Multiset[Cubeable] = Multiset()
        factored = OrderedDict()

        for cubeable, multiplicity in self.cubeables.items():
            amount = multiplicity * factor
            whole = int(amount)
            if whole:
                additionals.add(cubeable, whole)
            remainder = amount - whole
            if remainder:
                factored[cubeable] = remainder

        s = sum(factored.values())

        return self + self.__class__(additionals) + (
            self.__class__(
                choice(
                    list(factored.keys()),
                    remaining - len(additionals),
                    replace = False,
                    p = [v / s for v in factored.values()],
                )
            ) if s else self.__class__()
        )

    def __iter__(self) -> t.Iterator[C]:
        return self._cubeables.__iter__()

    def __len__(self) -> int:
        return len(self._cubeables)

    @abstractmethod
    def serialize(self) -> serialization_model:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> BaseCube:
        pass

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        for model in sorted(self.models, key = lambda _printing: _printing.id):
            yield str(model.id).encode('ASCII')
        for persistent_hash in sorted(
            lap.persistent_hash()
                for lap in
                self.laps
        ):
            yield persistent_hash.encode('ASCII')

    def __hash__(self) -> int:
        return hash(self._cubeables)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._cubeables == other._cubeables
        )

    def __add__(self, other: t.Union[BaseCubeableCollection, t.Iterable[Cubeable]]) -> BaseCube:
        if isinstance(other, BaseCubeableCollection):
            return self.__class__(
                self._cubeables + other.items
            )
        return self.__class__(
            self._cubeables + other
        )

    def __sub__(self, other: t.Union[BaseCubeableCollection, t.Iterable[Cubeable]]) -> BaseCube:
        if isinstance(other, BaseCubeableCollection):
            return self.__class__(
                self._cubeables - other.items
            )
        return self.__class__(
            self._cubeables - other
        )

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.__hash__()})'


B = t.TypeVar('B', bound = BaseCube)


class CardboardCube(
    BaseCube[CardboardCubeable, Cardboard, CardboardTrap, CardboardTicket, CardboardPurple, CardboardLap],
    CardboardCubeableCollection,
):

    @property
    def cardboard_cubeables(self) -> FrozenMultiset[CardboardCubeable]:
        return self._cubeables

    @property
    def cardboards(self) -> FrozenMultiset[Cardboard]:
        return self.models

    @property
    def all_cardboards(self) -> t.Iterator[Cardboard]:
        return self.all_models

    @property
    def garbage_cardboards(self) -> t.Iterator[Cardboard]:
        return self.garbage_models

    def serialize(self) -> serialization_model:
        return {
            'cardboards': self.cardboards,
            'traps': self.traps,
            'tickets': self.tickets,
            'purples': self.purples,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CardboardCube:
        return cls(
            cubeables = itertools.chain(
                inflator.inflate_all(Cardboard, value['cardboards']),
                (
                    CardboardTrap.deserialize(trap, inflator)
                    for trap in
                    value.get('traps', ())
                ),
                (
                    CardboardTicket.deserialize(ticket, inflator)
                    for ticket in
                    value.get('tickets', ())
                ),
                (
                    CardboardPurple.deserialize(purple, inflator)
                    for purple in
                    value.get('purples', ())
                ),
            )
        )


class Cube(
    BaseCube[Cubeable, Printing, Trap, Ticket, Purple, Lap],
    CubeableCollection,
):

    @property
    def as_cardboards(self) -> CardboardCube:
        return CardboardCube(
            (
                (cardboardize(cubeable), multiplicity)
                for cubeable, multiplicity in
                self._cubeables.items()
            )
        )

    @property
    def cubeables(self) -> FrozenMultiset[Cubeable]:
        return self._cubeables

    @property
    def printings(self) -> FrozenMultiset[Printing]:
        return self.models

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
                filter(
                    lambda p: p[1],
                    (
                        ('printings', self.printings),
                        ('traps', self.traps),
                        ('tickets', self.tickets),
                        ('purples', self.purples)
                    )
                )
        )

    @property
    def all_printings(self) -> t.Iterator[Printing]:
        return self.all_models

    @property
    def garbage_printings(self) -> t.Iterator[Printing]:
        return self.garbage_models

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
