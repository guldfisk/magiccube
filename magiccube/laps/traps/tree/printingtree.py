import typing as t

from abc import abstractmethod
import hashlib
import os

from lazy_property import LazyProperty
from PIL import Image, ImageDraw
from promise import Promise

from mtgorp.models.persistent.printing import Printing
from mtgorp.utilities.containers import HashableMultiset
from mtgorp.models.collections.serilization.serializeable import Serializeable, model_tree
from mtgimg.interface import ImageLoader

from magiccube import paths
from magiccube.laps import imageutils


class PrintingNode(Serializeable):

	def __init__(self, printings: t.Iterable[t.Union[Printing, 'PrintingNode']]):
		self._options = printings if isinstance(printings, HashableMultiset) else HashableMultiset(printings)
		self._persistent_hash = None

	@LazyProperty
	def name(self):
		return ''.join(
			(
				str(option[1]) + 'x'
				if option[1] > 1 else
				''
			)
			+ (
				option[0].cardboard.name
				if isinstance(option[0], Printing) else
				'({}({}))'.format(option[0].__class__.__name__, option[0].name)
			)
			for option in
			self.sorted_items
		)

	def persistent_hash(self) -> str:
		if self._persistent_hash is not None:
			return self._persistent_hash

		hasher = hashlib.sha512()
		hasher.update(self.__class__.__name__.encode('UTF-8'))

		for option in self._options:
			if isinstance(option, Printing):
				hasher.update(str(option.id).encode('ASCII'))
			else:
				hasher.update(option.persistent_hash().encode('UTF-8'))

		self._persistent_hash = hasher.hexdigest()

		return self._persistent_hash

	@LazyProperty
	def sorted_items(self) -> t.List[t.Tuple[t.Union[Printing, 'PrintingNode'], int]]:
		return sorted(
			self._options.items(),
			key = lambda p:
				p[0].cardboard.name
				if isinstance(p[0], Printing) else
				p[0].name
		)

	@LazyProperty
	def sorted_uniques(self) -> t.List[t.Tuple[t.Union[Printing, 'PrintingNode'], int]]:
		return sorted(
			self._options.distinct_elements(),
			key=lambda p:
			p.cardboard.name
			if isinstance(p, Printing) else
			p.name
		)

	@abstractmethod
	def get_image(self, loader: ImageLoader, width: int, height: int, **kwargs) -> Image.Image:
		pass

	def to_model_tree(self) -> model_tree:
		return {
			'options': [
				option
				if isinstance(option, Printing) else
				option.to_model_tree()
				for option in
				self._options
			],
			'type': self.__class__.__name__,
		}

	@classmethod
	def from_model_tree(cls, tree: model_tree) -> 'PrintingNode':
		return (
			AnyNode
			if tree['type'] == AnyNode.__name__ else
			AllNode
		)(
			option
			if isinstance(option, Printing) else
			cls.from_model_tree(option)
			for option in
			tree['options']
		)

	def __hash__(self):
		return hash((self.__class__, self._options))

	def __eq__(self, other):
		return (
			self.__class__ == other.__class__
			and self._options == other.options
		)

	def __repr__(self):
		return f'{self.__class__.__name__}({self._options})'


class BorderedNode(PrintingNode):
	BORDER_COLOR = (0, 0, 0)
	BORDER_WIDTH = 12
	FONT_PATH = os.path.join(paths.FONTS_DIRECTORY, 'Beleren-Bold.ttf')

	def _name_printing(self, printing: Printing) -> str:
		return (
			(
				str(self._options[printing]) + 'x '
				if self._options[printing] > 1 and len(self._options.distinct_elements()) > 1 else
				''
			)
			+ printing.cardboard.name
		)

	def get_image(
		self,
		loader: ImageLoader,
		width: int,
		height: int,
		bordered_sides: int = imageutils.ALL_SIDES
	) -> Image.Image:

		pictured_printings = (
			self._options
			if len(self._options.distinct_elements()) == 1 and isinstance(self.sorted_uniques[0], Printing) else
			self.sorted_uniques
		)

		images = Promise.all(
			tuple(
				loader.get_image(option, crop=True)
				if isinstance(option, Printing) else
				Promise.resolve(option)
				for option in
				pictured_printings
			)
		).get()

		background = Image.new('RGBA', (width, height), (0, 0, 0, 255))

		draw = ImageDraw.Draw(background)

		cx, cy, content_width, content_height = imageutils.shrunk_box(
			x = 0,
			y = 0,
			w = width,
			h = height,
			shrink = self.BORDER_WIDTH-1,
			sides = bordered_sides,
		)

		for span, option, image, in zip(
			imageutils.section(content_height, len(pictured_printings)),
			pictured_printings,
			images
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
					font_path = self.FONT_PATH,
				)
			else:
				background.paste(
					option.get_image(
						loader = loader,
						width = content_width,
						height = stop - start,
						bordered_sides = imageutils.LEFT_SIDE
					),
					(cx, start + cy)
				)

		imageutils.inline_box(
			draw = draw,
			box = (0, 0, width, height),
			color = self.BORDER_COLOR,
			width = self.BORDER_WIDTH + 1,
			sides = bordered_sides,
		)

		return background


class AllNode(BorderedNode):
	BORDER_COLOR = (50, 50, 50)


class AnyNode(BorderedNode):
	BORDER_COLOR = (170, 170, 170)
