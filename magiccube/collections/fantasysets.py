from __future__ import annotations

import typing as t
from abc import abstractmethod

from frozendict import frozendict

from yeetlong.multiset import FrozenMultiset

from mtgorp.models.limited.boostergen import BoosterMap, MapSlot
from mtgorp.models.serilization.serializeable import serialization_model, Inflator, Serializeable, PersistentHashable

from magiccube.collections.cube import BaseCube, Cube, CardboardCube
from magiccube.collections.cubeable import Cubeable


C = t.TypeVar('C', bound = BaseCube)


class BaseFantasySet(Serializeable, PersistentHashable, t.Generic[C]):

    def __init__(self, rarity_map: t.Mapping[str, C]):
        self._rarity_map: t.Mapping[str, C] = frozendict(rarity_map)

    @property
    def rarity_map(self) -> t.Mapping[str, C]:
        return self._rarity_map

    def serialize(self) -> serialization_model:
        return {
            'type': self.__class__.__name__,
            'rarity_map': {
                k: v.serialize()
                for k, v in
                self._rarity_map.items()
            }
        }

    @classmethod
    @abstractmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> BaseFantasySet:
        pass

    def __hash__(self) -> int:
        return hash(self._rarity_map)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._rarity_map == other._rarity_map
        )

    def _calc_persistent_hash(self) -> t.Iterator[t.ByteString]:
        for k, v in sorted(self._rarity_map.items(), key = lambda p: p[0]):
            yield k.encode('UTF-8')
            yield v.persistent_hash().encode('ASCII')

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(
                '{}: {}'.format(rarity, len(cube))
                for rarity, cube in
                self._rarity_map.items()
            ),
        )


class CardboardFantasySet(BaseFantasySet[CardboardCube]):

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CardboardFantasySet:
        return cls(
            {
                k: CardboardCube.deserialize(v, inflator)
                for k, v in
                value['rarity_map'].items()
            }
        )


class FantasySet(BaseFantasySet[Cube]):

    @property
    def as_cardboards(self) -> CardboardFantasySet:
        return CardboardFantasySet(
            {
                rarity: cards.as_cardboards
                for rarity, cards in
                self._rarity_map.items()
            }
        )

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> FantasySet:
        return cls(
            {
                k: Cube.deserialize(v, inflator)
                for k, v in
                value['rarity_map'].items()
            }
        )


class FantasyBoosterKeySlot(Serializeable, PersistentHashable):

    def __init__(self, key_map: t.Mapping[str, int]):
        self._key_map = frozendict(key_map)

    @property
    def key_map(self) -> t.Mapping[str, int]:
        return self._key_map

    def get_map_slot(self, fantasy_set: FantasySet) -> MapSlot[Cubeable]:
        return MapSlot(
            {
                fantasy_set.rarity_map.get(key).cubeables or FrozenMultiset(): weight
                for key, weight in
                self._key_map.items()
            }
        )

    def serialize(self) -> serialization_model:
        return {
            'type': self.__class__.__name__,
            'key_map': self._key_map,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> FantasyBoosterKeySlot:
        return cls(value['key_map'])

    def __hash__(self) -> int:
        return hash(self._key_map)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._key_map == other._key_map
        )

    def _calc_persistent_hash(self) -> t.Iterator[t.ByteString]:
        for k, v in sorted(self._key_map.items(), key = lambda p: p[0]):
            yield k.encode('UTF-8')
            yield str(v).encode('ASCII')

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(
                '{}: {}'.format(key, weight)
                for key, weight in
                self._key_map.items()
            ),
        )


class FantasyBoosterKey(Serializeable, PersistentHashable):

    def __init__(self, slots: t.Union[t.Iterable[FantasyBoosterKeySlot], t.Mapping[FantasyBoosterKeySlot, int]]):
        self._slots = slots if isinstance(slots, FrozenMultiset) else FrozenMultiset(slots)

    @property
    def slots(self) -> FrozenMultiset[FantasyBoosterKeySlot]:
        return self._slots

    def get_booster_map(self, fantasy_set: FantasySet) -> BoosterMap[Cubeable]:
        return BoosterMap(
            {
                slot.get_map_slot(fantasy_set): multiplicity
                for slot, multiplicity in
                self.slots.items()
            }
        )

    def serialize(self) -> serialization_model:
        return {
            'type': self.__class__.__name__,
            'slots': [
                (slot.serialize(), multiplicity)
                for slot, multiplicity in
                self._slots.items()
            ]
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> FantasyBoosterKey:
        return cls(
            FrozenMultiset(
                (FantasyBoosterKeySlot.deserialize(slot, inflator), multiplicity)
                for slot, multiplicity in
                value['slots']
            )
        )

    def __len__(self) -> int:
        return len(self._slots)

    def __hash__(self) -> int:
        return hash(self._slots)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._slots == other._slots
        )

    def _calc_persistent_hash(self) -> t.Iterator[t.ByteString]:
        for _hash, multiplicity in sorted(
            (
                (slot.persistent_hash(), multiplicity)
                for slot, multiplicity in
                self._slots.items()
            ),
            key = lambda p: p[0],
        ):
            yield _hash.encode('ASCII')
            yield str(multiplicity).encode('ASCII')

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            dict(self._slots.elements()),
        )
