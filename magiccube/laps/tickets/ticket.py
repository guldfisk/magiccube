from __future__ import annotations

import os
import typing as t
from abc import abstractmethod

import aggdraw
from mtgimg.interface import ImageLoader
from mtgorp.models.interfaces import Cardboard, Printing
from mtgorp.models.serilization.serializeable import Inflator, serialization_model
from orp.database import Model
from PIL import Image, ImageDraw
from promise import Promise

from magiccube import paths
from magiccube.laps import imageutils
from magiccube.laps.lap import BaseLap, CardboardLap, Lap


T = t.TypeVar("T", bound=Model)


class BaseTicket(BaseLap, t.Generic[T]):
    FONT_PATH = os.path.join(paths.FONTS_DIRECTORY, "Beleren-Bold.ttf")

    def __init__(self, options: t.Iterable[T], name: str):
        self._name = name
        self._options = frozenset(options)

    @property
    def name(self):
        return self._name

    @property
    def options(self) -> t.AbstractSet[Printing]:
        return self._options

    @property
    def description(self) -> str:
        return "Ticket"

    @property
    @abstractmethod
    def sorted_options(self) -> t.List[T]:
        pass

    def serialize(self) -> serialization_model:
        return {
            "options": self._options,
            "name": self._name,
            **super().serialize(),
        }

    def __hash__(self) -> int:
        return hash((self._options, self._name))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self._options == other.options and self._name == other.name

    def __iter__(self) -> t.Iterable[T]:
        return self._options.__iter__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._options})"


class CardboardTicket(BaseTicket[Cardboard], CardboardLap):
    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("UTF-8")
        yield self._name.encode("UTF-8")
        for s in sorted(str(option.id) for option in self._options):
            yield s.encode("UTF-8")

    @property
    def sorted_options(self) -> t.List[Cardboard]:
        return sorted(self._options, key=lambda c: c.name)

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CardboardTicket:
        return cls(
            inflator.inflate_all(Cardboard, value["options"]),
            value["name"],
        )


class Ticket(BaseTicket[Printing], Lap):
    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("UTF-8")
        yield self._name.encode("UTF-8")
        for s in sorted(str(option.id) for option in self._options):
            yield s.encode("ASCII")

    @property
    def as_cardboards(self) -> CardboardTicket:
        return CardboardTicket(
            (option.cardboard for option in self._options),
            self._name,
        )

    @property
    def sorted_options(self) -> t.List[Printing]:
        return sorted(self._options, key=lambda p: p.cardboard.name)

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> Ticket:
        return cls(
            inflator.inflate_all(Printing, value["options"]),
            value["name"],
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
            if image.width == width
            else image.resize(
                (
                    width,
                    image.height * width // image.width,
                ),
                Image.LANCZOS,
            )
            for image in Promise.all(
                tuple(loader.get_image(option, crop=True) for option in self.sorted_options)
            ).get()
        ]

        background = Image.new("RGBA", (width, height), (0, 0, 0, 255))

        draw = ImageDraw.Draw(background)

        for (
            span,
            option,
            image,
        ) in zip(
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
            draw=draw,
            name=self._name,
            box=(0, 0, width, height),
            font_path=self.FONT_PATH,
            font_size=60,
        )

        if crop:
            return background

        mask = Image.new("RGBA", (width, height), (0,) * 4)
        mask_agg_draw = aggdraw.Draw(mask)
        imageutils.filled_rounded_box(
            draw=mask_agg_draw,
            box=(0, 0, width, height),
            corner_radius=corner_radius,
            color=(255,) * 3,
        )

        return Image.composite(
            background,
            Image.new("RGBA", (width, height), (0, 0, 0, 0)),
            mask,
        )

    def get_image_name(self, back: bool = False, crop: bool = False) -> str:
        return self.persistent_hash()

    @classmethod
    def get_image_dir_name(cls) -> str:
        return "tickets"

    def has_back(self) -> bool:
        return False
