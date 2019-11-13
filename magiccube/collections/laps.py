from __future__ import annotations

import typing as t

from magiccube.laps.traps.trap import Trap
from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator, PersistentHashable
from yeetlong.multiset import FrozenMultiset


class TrapCollection(Serializeable, PersistentHashable):

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

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        for trap in self._traps:
            yield trap.persistent_hash().encode('ASCII')

    def __iter__(self) -> t.Iterator[Trap]:
        return self._traps.__iter__()

    def __len__(self):
        return self._traps.__len__()

    def __hash__(self) -> int:
        return hash(self._traps)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._traps == other._traps
        )