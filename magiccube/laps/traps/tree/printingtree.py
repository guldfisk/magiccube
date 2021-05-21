from __future__ import annotations

import itertools
import typing as t
import os

from abc import abstractmethod

from lazy_property import LazyProperty
from PIL import Image, ImageDraw
from promise import Promise
import aggdraw

from yeetlong.multiset import FrozenMultiset

from mtgorp.models.serilization.serializeable import Serializeable, PersistentHashable, serialization_model, Inflator
from mtgorp.models.interfaces import Printing, Cardboard

from mtgimg.interface import ImageLoader
from mtgimg import crop

from magiccube import paths
from magiccube.laps import imageutils


N = t.TypeVar('N')
T = t.TypeVar('T', bound = t.Union[Cardboard, Printing])


class BaseNode(Serializeable, PersistentHashable, t.Generic[N, T]):
    _MINIMAL_STRING_CONNECTOR: str
    _children: FrozenMultiset[t.Union[N, T]]

    @property
    def id(self):
        return self.persistent_hash()

    @property
    @abstractmethod
    def children(self) -> FrozenMultiset[t.Union[N, T]]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def get_minimal_string(self, **kwargs) -> str:
        pass

    @property
    @abstractmethod
    def sorted_items(self) -> t.List[t.Tuple[t.Union[N, T], int]]:
        pass

    def serialize(self) -> serialization_model:
        return {
            'options': [
                (child, multiplicity)
                for child, multiplicity in
                self._children.items()
            ],
            'type': self.__class__.__name__,
        }

    @property
    def flattened(self) -> t.Iterator[t.Union[T, NodeAny]]:
        if isinstance(self, NodeAny):
            yield self
        else:
            for child in self._children:
                if isinstance(child, BaseNode):
                    yield from child.flattened
                else:
                    yield child

    @property
    def flattened_options(self) -> t.Iterator[FrozenMultiset[T]]:
        if isinstance(self, NodeAny):
            for child in self._children:
                if isinstance(child, BaseNode):
                    yield from child.flattened_options
                else:
                    yield FrozenMultiset((child,))
        else:
            accumulated = []
            anys = []
            for child in self.flattened:
                if isinstance(child, BaseNode):
                    anys.append(child)
                else:
                    accumulated.append(child)

            for combination in itertools.product(
                *(
                    _any.flattened_options
                    for _any in
                    anys
                )
            ):
                yield FrozenMultiset(
                    itertools.chain(
                        accumulated,
                        *combination,
                    )
                )

    def __hash__(self) -> int:
        return hash((self.__class__, self._children))

    def __eq__(self, other: BaseNode) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._children == other._children
        )

    def __repr__(self):
        return f'{self.__class__.__name__}({self._children})'

    def __iter__(self) -> t.Iterator[T]:
        for child in self._children:
            if isinstance(child, BaseNode):
                yield from child
            else:
                yield child


class CardboardNode(BaseNode['CardboardNode', Cardboard]):
    flattened: t.Iterator[t.Union[Cardboard, CardboardAnyNode]]
    flattened_options: t.Iterator[FrozenMultiset[Cardboard]]

    def __init__(
        self,
        children: t.Union[
            t.Iterable[CardboardNodeChild],
            t.Mapping[CardboardNodeChild, int]
        ],
    ):
        self._children = FrozenMultiset(children)

    @property
    def sorted_items(self) -> t.List[t.Tuple[CardboardNodeChild, int]]:
        return sorted(
            self._children.items(),
            key = lambda p: p[0].name,
        )

    def get_minimal_string(self, **kwargs) -> str:
        return self._MINIMAL_STRING_CONNECTOR.join(
            (
                '({})'.format(
                    (f'{multiplicity}# ' if multiplicity > 1 else '')
                    + child.name
                    if isinstance(child, Cardboard) else
                    f'{child.get_minimal_string()}'
                )
                for child, multiplicity in
                self.sorted_items
            )
        )

    @property
    def children(self) -> FrozenMultiset[CardboardNodeChild]:
        return self._children

    @property
    def name(self) -> str:
        return ''.join(
            (
                str(multiplicity) + 'x'
                if multiplicity > 1 else
                ''
            )
            + (
                option.name
                if isinstance(option, Cardboard) else
                '{} {}'.format(
                    option.name,
                    option.__class__.__name__,
                )
            )
            for option, multiplicity in
            self.sorted_items
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode('UTF-8')
        for s in sorted(
            child.persistent_hash()
            if isinstance(child, BaseNode) else
            str(child.id)
            for child in
            self._children
        ):
            yield s.encode('UTF-8')

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CardboardNode:
        return (
            CardboardAnyNode
            if value['type'] == CardboardAnyNode.__name__ else
            CardboardAllNode
        )(

            {
                (
                    inflator.inflate(Cardboard, child)
                    if isinstance(child, str) else
                    cls.deserialize(child, inflator)
                ):
                    multiplicity
                for child, multiplicity
                in value['options']
            }
        )


class NodeBranch(BaseNode):
    _MINIMAL_STRING_CONNECTOR: str


class NodeAll(NodeBranch):
    _MINIMAL_STRING_CONNECTOR = '; '


class NodeAny(NodeBranch):
    _MINIMAL_STRING_CONNECTOR = ' || '


class CardboardAllNode(CardboardNode, NodeAll):
    pass


class CardboardAnyNode(CardboardNode, NodeAny):
    pass


class PrintingNode(BaseNode['PrintingNode', Printing]):
    _children: FrozenMultiset[PrintingNodeChild]
    _CARDBOARD_EQUIVALENT = CardboardNode

    flattened: t.Iterator[t.Union[Printing, AnyNode]]
    flattened_options: t.Iterator[FrozenMultiset[Printing]]

    def __init__(
        self,
        children: t.Union[
            t.Iterable[PrintingNodeChild],
            t.Mapping[PrintingNodeChild, int]
        ],
    ):
        self._children = FrozenMultiset(children)

    @property
    def children(self) -> FrozenMultiset[PrintingNodeChild]:
        return self._children

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode('UTF-8')
        for s in sorted(
            child.persistent_hash()
            if isinstance(child, BaseNode) else
            str(child.id)
            for child in
            self._children
        ):
            yield s.encode('ASCII')

    @property
    def as_cardboards(self) -> CardboardNode:
        return self._CARDBOARD_EQUIVALENT(
            child.cardboard
            if isinstance(child, Printing) else
            child.as_cardboards
            for child in
            self._children
        )

    def get_minimal_string(self, identified_by_id: bool = True) -> str:
        return self._MINIMAL_STRING_CONNECTOR.join(
            (
                '({})'.format(
                    (f'{multiplicity}# ' if multiplicity > 1 else '')
                    + f'{child.cardboard.name}|{child.id if identified_by_id else child.expansion.code}'
                    if isinstance(child, Printing) else
                    f'{child.get_minimal_string(identified_by_id)}'
                )
                for child, multiplicity in
                self.sorted_items
            )
        )

    @LazyProperty
    def name(self):
        return ''.join(
            (
                str(multiplicity) + 'x'
                if multiplicity > 1 else
                ''
            )
            + (
                option.cardboard.name
                if isinstance(option, Printing) else
                '{} {}'.format(
                    option.name,
                    option.__class__.__name__,
                )
            )
            for option, multiplicity in
            self.sorted_items
        )

    @LazyProperty
    def sorted_items(self) -> t.List[t.Tuple[PrintingNodeChild, int]]:
        return sorted(
            self._children.items(),
            key = lambda p:
            p[0].cardboard.name
            if isinstance(p[0], Printing) else
            p[0].name
        )

    @property
    def imageds(self) -> t.Iterator[t.Union[Printing, PrintingNode]]:
        return itertools.chain(
            *(
                itertools.repeat(item, 1 if isinstance(item, Printing) else multiplicity)
                for item, multiplicity in
                self._children.items()
            )
        )

    @LazyProperty
    def sorted_imageds(self) -> t.List[PrintingNodeChild]:
        return sorted(
            list(self.imageds),
            key = lambda p:
            p.cardboard.name
            if isinstance(p, Printing) else
            p.name
        )

    @LazyProperty
    def sorted_uniques(self) -> t.List[PrintingNodeChild]:
        return sorted(
            self._children.distinct_elements(),
            key = lambda p:
            p.cardboard.name
            if isinstance(p, Printing) else
            p.name
        )

    @abstractmethod
    def get_image(self, loader: ImageLoader, width: int, height: int, **kwargs) -> Image.Image:
        pass

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> PrintingNode:
        return (
            AnyNode
            if value['type'] == AnyNode.__name__ else
            AllNode
        )(

            {
                (
                    inflator.inflate(Printing, child)
                    if isinstance(child, int) else
                    cls.deserialize(child, inflator)
                ):
                    multiplicity
                for child, multiplicity
                in value['options']
            }
        )

    @property
    def image_amount(self) -> int:
        return sum(
            1 if isinstance(child, Printing) else multiplicity * child.image_amount
            for child, multiplicity in
            self._children.items()
        )


BaseNodeChild = t.Union[BaseNode, Printing, Cardboard]
CardboardNodeChild = t.Union[CardboardNode, Cardboard]
PrintingNodeChild = t.Union[PrintingNode, Printing]


class BorderedNode(PrintingNode):
    _BORDER_COLOR = (0, 0, 0)
    _BORDER_TRIANGLE_COLOR = (255, 255, 255)
    _BORDER_WIDTH = 12
    _FONT_PATH = os.path.join(paths.FONTS_DIRECTORY, 'Beleren-Bold.ttf')
    _FULL_WIDTH = crop.CROPPED_SIZE[0]

    def _name_printing(self, printing: Printing) -> str:
        return (
            (
                str(self._children[printing]) + 'x '
                if self._children[printing] > 1 else
                ''
            )
            + printing.cardboard.name
        )

    def get_printing_at(self, x: float, y: float, width: float, height: float, bordered_sides: int) -> Printing:
        top_offset = self._BORDER_WIDTH if bordered_sides & imageutils.TOP_SIDE else 0
        bottom_offset = self._BORDER_WIDTH if bordered_sides & imageutils.BOTTOM_SIDE else 0

        content_height = height - top_offset - bottom_offset
        item_height = content_height / len(self.sorted_imageds)

        if y <= top_offset:
            item = self.sorted_imageds[0]
            remainder = 0

        elif y >= height - bottom_offset:
            item = self.sorted_imageds[-1]
            remainder = item_height

        else:
            floating_index = (y - top_offset) / content_height * len(self.sorted_imageds)
            _index = int(floating_index)
            remainder = (floating_index - _index) * content_height
            item = self.sorted_imageds[_index]

        if isinstance(item, Printing):
            return item

        return item.get_printing_at(x, remainder, width, content_height, imageutils.LEFT_SIDE)

    def get_image(
        self,
        loader: ImageLoader,
        width: int,
        height: int,
        bordered_sides: int = imageutils.ALL_SIDES,
        triangled = True,
    ) -> Image.Image:

        pictured_printings = self.sorted_imageds

        images = [
            image.resize(
                (
                    width,
                    image.height * width // image.width,
                ),
                Image.LANCZOS,
            )
            if isinstance(image, Image.Image) and image.width != width else
            image
            for image in
            Promise.all(
                tuple(
                    loader.get_image(option, crop = True)
                    if isinstance(option, Printing) else
                    Promise.resolve(option)
                    for option in
                    pictured_printings
                )
            ).get()
        ]

        background = Image.new('RGBA', (width, height), (0, 0, 0, 255))

        draw = ImageDraw.Draw(background)

        cx, cy, content_width, content_height = imageutils.shrunk_box(
            x = 0,
            y = 0,
            w = width,
            h = height,
            shrink = self._BORDER_WIDTH - 1,
            sides = bordered_sides,
        )

        font_size = 27 + int(27 * min(width, self._FULL_WIDTH) / self._FULL_WIDTH)
        for span, option, image, in zip(
            imageutils.section(content_height, len(pictured_printings)),
            pictured_printings,
            images,
        ):
            start, stop = span
            if isinstance(option, Printing):
                background.paste(
                    imageutils.fit_image(image, content_width, stop - start + 1),
                    (cx, start + cy),
                )
                imageutils.draw_name(
                    draw = draw,
                    name = self._name_printing(option),
                    box = (
                        cx,
                        start + cy,
                        content_width,
                        stop - start,
                    ),
                    font_path = self._FONT_PATH,
                    font_size = font_size,
                )
            else:
                background.paste(
                    option.get_image(
                        loader = loader,
                        width = content_width,
                        height = stop - start,
                        bordered_sides = imageutils.LEFT_SIDE,
                        triangled = True,
                    ),
                    (cx, start + cy),
                )

        agg_draw = aggdraw.Draw(background)

        if triangled:
            imageutils.triangled_inlined_box(
                draw = agg_draw,
                box = (0, 0, width, height),
                color = self._BORDER_COLOR,
                bar_color = self._BORDER_TRIANGLE_COLOR,
                width = self._BORDER_WIDTH,
                triangle_length = self._BORDER_WIDTH,
                sides = bordered_sides,
            )

        else:
            imageutils.inline_box(
                draw = agg_draw,
                box = (0, 0, width, height),
                color = self._BORDER_COLOR,
                width = self._BORDER_WIDTH,
                sides = bordered_sides,
            )

        return background


ALL_COLOR = (50, 50, 50)
ANY_COLOR = (170, 170, 170)


class AllNode(BorderedNode, NodeAll):
    _CARDBOARD_EQUIVALENT = CardboardAllNode

    _BORDER_COLOR = ALL_COLOR
    _BORDER_TRIANGLE_COLOR = ANY_COLOR


class AnyNode(BorderedNode, NodeAny):
    _CARDBOARD_EQUIVALENT = CardboardAnyNode

    _BORDER_COLOR = ANY_COLOR
    _BORDER_TRIANGLE_COLOR = ALL_COLOR
