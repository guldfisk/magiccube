from __future__ import annotations

import typing as t

from mtgorp.models.collections.cardboardset import CardboardSet
from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator, PersistentHashable


class Infinites(CardboardSet):

    def __or__(self, other: t.Union[Infinites, InfinitesDeltaOperation]) -> Infinites:
        if isinstance(other, InfinitesDeltaOperation):
            return self.__class__((self._cardboards | other.added.cardboards) - other.removed.cardboards)
        return super().__or__(other)

    __add__ = __or__

    def __sub__(self, other: t.Union[Infinites, InfinitesDeltaOperation]) -> Infinites:
        if isinstance(other, InfinitesDeltaOperation):
            return self.__class__((self._cardboards | other.removed.cardboards) - other.added.cardboards)
        return super().__sub__(other)


class InfinitesDeltaOperation(Serializeable, PersistentHashable):

    def __init__(
        self,
        added: t.Optional[CardboardSet] = None,
        removed: t.Optional[CardboardSet] = None,
    ):
        self._added = added or CardboardSet()
        self._removed = removed or CardboardSet()

    @classmethod
    def from_change(cls, from_infinites: Infinites, to_infinites: Infinites) -> InfinitesDeltaOperation:
        return cls(
            to_infinites - from_infinites,
            from_infinites - to_infinites,
        )

    @property
    def added(self) -> CardboardSet:
        return self._added

    @property
    def removed(self) -> CardboardSet:
        return self._removed

    def serialize(self) -> serialization_model:
        return {
            'added': self._added,
            'removed': self._removed,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> InfinitesDeltaOperation:
        return cls(
            CardboardSet.deserialize(value['added'], inflator),
            CardboardSet.deserialize(value['removed'], inflator),
        )

    def __hash__(self) -> int:
        return hash((self._added, self._removed))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._added == other._added
            and self._removed == other._removed
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        for n in sorted((c.name for c in self._added)):
            yield n.encode('UTF-8')
        for n in sorted((c.name for c in self._removed)):
            yield n.encode('UTF-8')

    def __repr__(self) -> str:
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self._added,
            self._removed,
        )

    def __add__(self, other: InfinitesDeltaOperation) -> InfinitesDeltaOperation:
        add = self._added | other.added
        remove = self._removed | other.removed
        intersection = add & remove
        return self.__class__(
            add - intersection,
            remove - intersection,
        )

    def __sub__(self, other: InfinitesDeltaOperation) -> InfinitesDeltaOperation:
        add = self._added | other.removed
        remove = self._removed | other.added
        intersection = add & remove
        return self.__class__(
            add - intersection,
            remove - intersection,
        )
