from __future__ import annotations

import typing as t

from magiccube.laps.traps.trap import Trap
from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator
from yeetlong.multiset import FrozenMultiset


class TrapCollection(Serializeable):

    def __init__(self, traps: t.Iterable[Trap]):
        self._traps = traps if isinstance(traps, FrozenMultiset) else FrozenMultiset(traps)

    @property
    def traps(self) -> FrozenMultiset[Trap]:
        return self._traps

    def serialize(self) -> serialization_model:
        return {
            'traps': [
                (lap, multiplicity)
                for lap, multiplicity
                in self._traps.items()
            ]
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> TrapCollection:
        return cls(
            FrozenMultiset(
                {
                    Trap.deserialize(trap, inflator):
                        multiplicity
                    for trap, multiplicity in
                    value['traps']
                }
            ),
        )

    def __hash__(self) -> int:
        return hash(self._traps)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._traps == other._traps
        )