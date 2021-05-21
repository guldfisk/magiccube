from __future__ import annotations

import typing as t
from enum import Enum
from abc import abstractmethod

import aggdraw
from PIL import Image

from mtgorp.models.serilization.serializeable import serialization_model, Inflator
from mtgorp.models.interfaces import Printing, Cardboard

from mtgimg.interface import ImageLoader

from magiccube.laps import imageutils
from magiccube.laps.lap import Lap, CardboardLap, BaseLap
from magiccube.laps.traps.tree.printingtree import BorderedNode, CardboardNode, BaseNode


N = t.TypeVar('N', bound = BaseNode)
T = t.TypeVar('T', bound = t.Union[Cardboard, Printing])


class IntentionType(Enum):
    SYNERGY = 'synergy'
    OR = 'or'
    GARBAGE = 'garbage'
    LAND_GARBAGE = 'land_garbage'
    NO_INTENTION = 'no_intention'


class BaseTrap(BaseLap, t.Generic[N, T]):
    _node: N
    _intention_type: IntentionType

    def __init__(self, node: N, intention_type: IntentionType = IntentionType.NO_INTENTION):
        self._node = node
        self._intention_type = intention_type

    @property
    def node(self) -> N:
        return self._node

    @property
    def intention_type(self) -> t.Optional[IntentionType]:
        return self._intention_type

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    def serialize(self) -> serialization_model:
        return {
            'node': self._node.serialize(),
            'intention_type': self._intention_type.name,
            **super().serialize(),
        }

    @classmethod
    @abstractmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> Trap:
        pass

    def __hash__(self) -> int:
        return hash((self._node, self._intention_type))

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self._node.persistent_hash().encode('ASCII')
        yield self.__class__.__name__.encode('UTF-8')
        yield self._intention_type.name.encode('UTF-8')

    def __eq__(self, other: BaseTrap) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._node == other._node
            and self._intention_type == other._intention_type
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._intention_type.value}, {self._node})'

    def __iter__(self) -> t.Iterator[T]:
        return self._node.__iter__()

    def __contains__(self, item: T) -> bool:
        return item in self.__iter__()


class CardboardTrap(BaseTrap[CardboardNode, Cardboard], CardboardLap):

    @property
    def description(self) -> str:
        return self._node.get_minimal_string()

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CardboardTrap:
        return cls(
            CardboardNode.deserialize(
                value['node'],
                inflator,
            ),
            IntentionType[value['intention_type']] if 'intention_type' in value else None,
        )


class Trap(BaseTrap[BorderedNode, Printing], Lap):

    @property
    def as_cardboards(self) -> CardboardTrap:
        return CardboardTrap(
            node = self._node.as_cardboards,
            intention_type = self._intention_type,
        )

    @property
    def description(self) -> str:
        return self._node.get_minimal_string(identified_by_id = False)

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> Trap:
        return cls(
            BorderedNode.deserialize(
                value['node'],
                inflator,
            ),
            IntentionType[value['intention_type']] if 'intention_type' in value else None,
        )

    def get_printing_at(self, x: float, y: float, width: float, height: float) -> Printing:
        return self._node.get_printing_at(x, y, width, height, imageutils.HORIZONTAL_SIDES)

    def get_image(
        self,
        size: t.Tuple[int, int],
        loader: ImageLoader,
        back: bool = False,
        crop: bool = False,
    ) -> Image.Image:
        width, height = size
        corner_radius = max(2, height // 23)

        image = self._node.get_image(
            loader = loader,
            width = width,
            height = height,
            bordered_sides = imageutils.HORIZONTAL_SIDES,
            triangled = False,
        )

        if crop:
            return image

        mask = Image.new('RGBA', (width, height), (0,) * 4)
        mask_agg_draw = aggdraw.Draw(mask)
        imageutils.filled_rounded_box(
            draw = mask_agg_draw,
            box = (0, 0, width, height),
            corner_radius = corner_radius,
            color = (255,) * 3,
        )

        return Image.composite(
            image,
            Image.new('RGBA', (width, height), (0, 0, 0, 0)),
            mask,
        )

    def get_image_name(self, back: bool = False, crop: bool = False) -> str:
        return self.persistent_hash()

    @classmethod
    def get_image_dir_name(cls) -> str:
        return 'cube_traps'

    def has_back(self) -> bool:
        return False
