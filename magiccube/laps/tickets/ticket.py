import typing as t
import os

from PIL import Image, ImageDraw
import aggdraw
from promise import Promise
from lazy_property import LazyProperty

from mtgorp.models.persistent.printing import Printing

from mtgorp.models.serilization.serializeable import serialization_model, Inflator

from mtgimg.interface import ImageLoader

from magiccube.laps.lap import Lap
from magiccube.laps import imageutils
from magiccube import paths


class Ticket(Lap):

    FONT_PATH = os.path.join(paths.FONTS_DIRECTORY, 'Beleren-Bold.ttf')

    def __init__(self, printings: t.Iterable[Printing], name: str):
        self._name  = name
        self._options = frozenset(printings)

    @property
    def name(self):
        return self._name

    @property
    def options(self) -> t.AbstractSet[Printing]:
        return self._options

    @property
    def description(self) -> str:
        return 'Ticket'

    @LazyProperty
    def sorted_options(self) -> t.List[Printing]:
        return sorted(self._options, key=lambda p: p.cardboard.name)

    def serialize(self) -> serialization_model:
        return {
            'options': self._options,
            'name': self._name,
            **super().serialize(),
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> 'Ticket':
        return cls(
            inflator.inflate_all(Printing, value['options']),
            value['name'],
        )

    def get_image(
        self,
        size: t.Tuple[int, int],
        loader: ImageLoader,
        back: bool = False,
        crop: bool = False,
    ) -> Image.Image:

        width, height = size
        corner_radius = max(2, height // 23)

        images = [
            image
            if image.width == width else
            image.resize(
                (
                    width,
                    image.height * width // image.width,
                ),
                Image.LANCZOS,
            )
            for image in
            Promise.all(
                tuple(
                    loader.get_image(option, crop=True)
                    for option in
                    self.sorted_options
                )
            ).get()
        ]

        background = Image.new('RGBA', (width, height), (0, 0, 0, 255))

        draw = ImageDraw.Draw(background)

        for span, option, image, in zip(
            imageutils.section(height, len(self._options)),
            self._options,
            images,
        ):
            start, stop = span
            if isinstance(option, Printing):
                background.paste(
                    imageutils.fit_image(image, width, stop - start + 1),
                    (0, start),
                )

        imageutils.draw_name(
            draw = draw,
            name = self._name,
            box = (0, 0, width, height),
            font_path = self.FONT_PATH,
            font_size = 60,
        )

        if crop:
            return background

        mask = Image.new('RGBA', (width, height), (0,) * 4)
        mask_agg_draw = aggdraw.Draw(mask)
        imageutils.filled_rounded_box(
            draw=mask_agg_draw,
            box=(0, 0, width, height),
            corner_radius=corner_radius,
            color=(255,) * 3,
        )

        return Image.composite(
            background,
            Image.new('RGBA', (width, height), (0, 0, 0, 0)),
            mask,
        )

    def get_image_name(self, back: bool = False, crop: bool = False) -> str:
        return self.persistent_hash()

    @classmethod
    def get_image_dir_name(cls) -> str:
        return 'tickets'

    def has_back(self) -> bool:
        return False

    def __hash__(self) -> int:
        return hash((self._options, self._name))

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode('UTF-8')
        yield self._name.encode('UTF-8')
        for s in sorted(
            str(option.id)
            for option in
            self._options
        ):
            yield s.encode('ASCII')

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._options == other.options
            and self._name == other.name
        )

    def __iter__(self) -> t.Iterable[Printing]:
        return self._options.__iter__()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._options})'
