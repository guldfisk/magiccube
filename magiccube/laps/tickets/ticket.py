import typing as t

import hashlib
import os

from PIL import Image, ImageDraw
from promise import Promise
from lazy_property import LazyProperty

from mtgorp.models.persistent.printing import Printing

from mtgorp.models.collections.serilization.serializeable import model_tree

from mtgimg.interface import ImageLoader

from magiccube.laps.lap import Lap
from magiccube.laps import imageutils
from magiccube import paths


class Ticket(Lap):
	FONT_PATH = os.path.join(paths.FONTS_DIRECTORY, 'Beleren-Bold.ttf')

	def __init__(self, printings: t.Iterable[Printing], name: str):
		self._name  = name
		self._options = frozenset(printings)
		self._persistent_hash = None #type: str

	@property
	def name(self):
		return self._name

	@property
	def options(self) -> t.AbstractSet[Printing]:
		return self._options

	@LazyProperty
	def sorted_options(self) -> t.List[Printing]:
		return sorted(self._options, key=lambda p: p.cardboard.name)

	def to_model_tree(self) -> model_tree:
		return {
			'options': self._options,
			'name': self._name,
		}

	@classmethod
	def from_model_tree(cls, tree: model_tree) -> 'Ticket':
		return cls(tree['options'], tree['name'])

	def get_image(
		self,
		size: t.Tuple[int, int],
		loader: ImageLoader,
		back: bool = False,
		crop: bool = False,
	) -> Image.Image:

		width, height = size

		images = Promise.all(
			tuple(
				loader.get_image(option, crop=True)
				for option in
				self.sorted_options
			)
		).get()

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
			font_size = 40,
		)

		return background

	def get_image_name(self, back: bool = False, crop: bool = False) -> str:
		if self._persistent_hash is not None:
			return self._persistent_hash

		hasher = hashlib.sha512()

		hasher.update(self.__class__.__name__.encode('UTF-8'))
		hasher.update(self._name.encode('UTF-8'))

		for option in self._options:
			hasher.update(str(option.id).encode('ASCII'))

		self._persistent_hash = hasher.hexdigest()

		return self._persistent_hash

	def get_image_dir_name(self) -> str:
		return 'tickets'

	def has_back(self) -> bool:
		return False

	def __hash__(self) -> int:
		return hash((self._options, self._name))

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
