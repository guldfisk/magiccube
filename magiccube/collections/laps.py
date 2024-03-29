from __future__ import annotations

import typing as t

from mtgorp.models.serilization.serializeable import (
    Inflator,
    PersistentHashable,
    Serializeable,
    serialization_model,
)
from yeetlong.multiset import FrozenMultiset

from magiccube.laps.traps.trap import Trap


class TrapCollection(Serializeable, PersistentHashable):
    def __init__(self, traps: t.Iterable[Trap]):
        self._traps = traps if isinstance(traps, FrozenMultiset) else FrozenMultiset(traps)

    @property
    def traps(self) -> FrozenMultiset[Trap]:
        return self._traps

    def serialize(self) -> serialization_model:
        return {"traps": [(lap, multiplicity) for lap, multiplicity in self._traps.items()]}

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> TrapCollection:
        return cls(
            FrozenMultiset({Trap.deserialize(trap, inflator): multiplicity for trap, multiplicity in value["traps"]}),
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        for trap in self._traps:
            yield trap.persistent_hash().encode("ASCII")

    def __iter__(self) -> t.Iterator[Trap]:
        return self._traps.__iter__()

    def __len__(self):
        return self._traps.__len__()

    def __hash__(self) -> int:
        return hash(self._traps)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self._traps == other._traps

    def __sub__(self, other: TrapCollection) -> TrapCollection:
        return TrapCollection(self._traps - other._traps)

    __rsub__ = __sub__

    def __add__(self, other: TrapCollection) -> TrapCollection:
        return TrapCollection(self._traps + other._traps)

    __radd__ = __add__
