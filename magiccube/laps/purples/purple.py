import typing as t

import os
import hashlib

from PIL import Image, ImageDraw
import aggdraw

from mtgorp.models.serilization.serializeable import serialization_model, Inflator

from mtgimg.interface import ImageLoader

from magiccube.laps.lap import Lap
from magiccube.laps import imageutils
from magiccube import paths


class Purple(Lap):

	_FONT_PATH = os.path.join(paths.FONTS_DIRECTORY, 'Beleren-Bold.ttf')

	def __init__(self, name: str, description: str = ''):
		self._name = name
		self._description = description

		self._persistent_hash = None

	@property
	def name(self) -> str:
		return self._name

	@property
	def description(self) -> str:
		return self._description

	def __hash__(self) -> int:
		return hash(self._name)

	def __eq__(self, other: object) -> bool:
		return (
			isinstance(other, self.__class__)
			and self._name == other._name
		)

	def serialize(self) -> serialization_model:
		return {
			'name': self._name,
			'description': self._description,
		}

	@classmethod
	def deserialize(cls, value: serialization_model, inflator: Inflator) -> 'Purple':
		return cls(value['name'], value.get('description', ''))

	def get_image(
		self,
		size: t.Tuple[int, int],
		loader: 'ImageLoader',
		back: bool = False,
		crop: bool = False,
	) -> Image.Image:

		# width, height = 560, 435 if crop else 784
		width, height = size

		background = Image.new('RGBA', (width, height), (71, 57, 74, 255))

		agg_draw = aggdraw.Draw(background)
		draw = ImageDraw.Draw(background)

		border_line_width = max(2, height // 28)
		corner_radius = max(2, height // 23)

		imageutils.rounded_corner_box(
			draw = agg_draw,
			box= (0, 0, width, height),
			corner_radius = corner_radius,
			line_width = border_line_width,
			line_color = (30, 30, 30),
		)

		imageutils.draw_name(
			draw = draw,
			box = (
				0 + border_line_width,
				0 + border_line_width,
				width - border_line_width * 2,
				height - border_line_width * 2,
			),
			font_path = self._FONT_PATH,
			font_size = 70,
			name = self._name,
		)

		if crop:
			return background

		mask = Image.new('RGBA', (width, height), (0,) * 4)
		mask_agg_draw = aggdraw.Draw(mask)
		imageutils.filled_rounded_box(
			draw = mask_agg_draw,
			box = (0, 0, width, height),
			corner_radius = corner_radius,
			color = (255,) * 3,
		)

		return Image.composite(
			background,
			Image.new('RGBA', (width, height), (0, 0, 0, 0)),
			mask,
		)

	def get_image_name(self, back: bool = False, crop: bool = False) -> str:
		return self.persistent_hash()
		
	def persistent_hash(self) -> str:
		if self._persistent_hash is not None:
			return self._persistent_hash

		hasher = hashlib.sha512()

		hasher.update(self._name.encode('UTF-8'))

		self._persistent_hash = hasher.hexdigest()

		return self._persistent_hash

	@classmethod
	def get_image_dir_name(cls) -> str:
		return 'purples'

	def has_back(self) -> bool:
		return False

	def __str__(self) -> str:
		return f'{self.__class__.__name__}({self._name})'

