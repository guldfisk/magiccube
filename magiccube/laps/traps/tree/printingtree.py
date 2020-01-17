from __future__ import annotations

import typing as t
import os

from abc import abstractmethod

from lazy_property import LazyProperty
from PIL import Image, ImageDraw
from promise import Promise
import aggdraw

from yeetlong.multiset import FrozenMultiset

from mtgorp.models.persistent.printing import Printing
from mtgorp.models.serilization.serializeable import Serializeable, PersistentHashable, serialization_model, Inflator
from mtgimg.interface import ImageLoader
from mtgimg import crop

from magiccube import paths
from magiccube.laps import imageutils


class PrintingNode(Serializeable, PersistentHashable):
    _MINIMAL_STRING_CONNECTOR: str = None

    def __init__(
        self,
        children: t.Union[
            t.Iterable[NodeChild],
            t.Mapping[NodeChild, int]
        ],
    ):
        self._children = FrozenMultiset(children)

    @property
    def children(self) -> FrozenMultiset[NodeChild]:
        return self._children

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

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode('UTF-8')
        for s in sorted(
            str(child.id)
            if isinstance(child, Printing)
            else child.persistent_hash()
            for child in
            self._children
        ):
            yield s.encode('ASCII')

    @LazyProperty
    def sorted_items(self) -> t.List[t.Tuple[NodeChild, int]]:
        return sorted(
            self._children.items(),
            key = lambda p:
            p[0].cardboard.name
            if isinstance(p[0], Printing) else
            p[0].name
        )

    @LazyProperty
    def sorted_uniques(self) -> t.List[NodeChild]:
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

    def serialize(self) -> serialization_model:
        return {
            'options': [
                (child, multiplicity)
                for child, multiplicity in
                self._children.items()
            ],
            'type': self.__class__.__name__,
        }

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
    def flattened(self) -> t.Iterator[t.Union[Printing, AnyNode]]:
        for child in self._children:
            if isinstance(child, Printing) or isinstance(child, AnyNode):
                yield child
            else:
                yield from child 

    def __hash__(self):
        return hash((self.__class__, self._children))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self._children == other._children
        )

    def __iter__(self) -> t.Iterator[Printing]:
        for child in self._children:
            if isinstance(child, Printing):
                yield child
            else:
                yield from child

    def __repr__(self):
        return f'{self.__class__.__name__}({self._children})'


NodeChild = t.Union[PrintingNode, Printing]


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

    def get_image(
        self,
        loader: ImageLoader,
        width: int,
        height: int,
        bordered_sides: int = imageutils.ALL_SIDES,
        triangled = True,
    ) -> Image.Image:

        pictured_printings = self.sorted_uniques

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


class AllNode(BorderedNode):
    _MINIMAL_STRING_CONNECTOR = '; '

    _BORDER_COLOR = ALL_COLOR
    _BORDER_TRIANGLE_COLOR = ANY_COLOR


class AnyNode(BorderedNode):
    _MINIMAL_STRING_CONNECTOR = ' || '

    _BORDER_COLOR = ANY_COLOR
    _BORDER_TRIANGLE_COLOR = ALL_COLOR
