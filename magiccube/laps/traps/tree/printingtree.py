import typing as t

from abc import abstractmethod
import hashlib
import os

from lazy_property import LazyProperty
from PIL import Image, ImageDraw
from promise import Promise
import aggdraw

from mtgorp.models.persistent.printing import Printing
from mtgorp.utilities.containers import HashableMultiset
from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator
from mtgimg.interface import ImageLoader

from magiccube import paths
from magiccube.laps import imageutils


class PrintingNode(Serializeable):
	_MINIMAL_STRING_CONNECTOR = None #type: str

	def __init__(self, children: t.Iterable[t.Union[Printing, 'PrintingNode']]):
		self._children = HashableMultiset(children)
		self._persistent_hash = None

	@property
	def children(self) -> HashableMultiset[t.Union[Printing, 'PrintingNode']]:
		return self._children

	@property
	def minimal_string(self) -> str:
		return self._MINIMAL_STRING_CONNECTOR.join(
			(f'{multiplicity}# ' if multiplicity > 1 else '')
			+ f'{child.cardboard.name}|{child.id}'
			if isinstance(child, Printing) else
			f'({child.minimal_string})'
			for child, multiplicity in
			sorted(
				self._children.items(),
				key = lambda item: str(item[0]),
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

	def persistent_hash(self) -> str:
		if self._persistent_hash is not None:
			return self._persistent_hash

		hasher = hashlib.sha512()
		hasher.update(self.__class__.__name__.encode('UTF-8'))

		for option in self._children:
			if isinstance(option, Printing):
				hasher.update(str(option.id).encode('ASCII'))
			else:
				hasher.update(option.persistent_hash().encode('UTF-8'))

		self._persistent_hash = hasher.hexdigest()

		return self._persistent_hash

	@LazyProperty
	def sorted_items(self) -> t.List[t.Tuple[t.Union[Printing, 'PrintingNode'], int]]:
		return sorted(
			self._children.items(),
			key = lambda p:
				p[0].cardboard.name
				if isinstance(p[0], Printing) else
				p[0].name
		)

	@LazyProperty
	def sorted_uniques(self) -> t.List[t.Tuple[t.Union[Printing, 'PrintingNode'], int]]:
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
				'options': self._children,
				'type': self.__class__.__name__,
			}

	@classmethod
	def deserialize(cls, value: serialization_model, inflator: Inflator) -> 'PrintingNode':
		return (
				AnyNode
				if value['type'] == AnyNode.__name__ else
				AllNode
			)(
				inflator.inflate(Printing, option)
				if isinstance(option, int) else
				cls.deserialize(option, inflator)
				for option in
				value['options']
			)

	def __hash__(self):
		return hash((self.__class__, self._children))

	def __eq__(self, other):
		return (
			isinstance(other, self.__class__)
			and self._children == other._children
		)

	def __iter__(self) -> t.Iterable[Printing]:
		for option in self._children:
			if isinstance(option, Printing):
				yield option
			else:
				for item in option:
					yield item


	def __repr__(self):
		return f'{self.__class__.__name__}({self._children})'


class BorderedNode(PrintingNode):
	_BORDER_COLOR = (0, 0, 0)
	_BORDER_TRIANGLE_COLOR = (255, 255, 255)
	_BORDER_WIDTH = 12
	_FONT_PATH = os.path.join(paths.FONTS_DIRECTORY, 'Beleren-Bold.ttf')

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

		# pictured_printings = (
		# 	self._children
		# 	if len(self._children.distinct_elements()) == 1 and isinstance(self.sorted_uniques[0], Printing) else
		# 	self.sorted_uniques
		# )

		pictured_printings = self.sorted_uniques

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
			shrink =self._BORDER_WIDTH - 1,
			sides = bordered_sides,
		)

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
					font_size = 40,
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


_ALL_COLOR = (50, 50 ,50)
_ANY_COLOR = (170, 170, 170)


class AllNode(BorderedNode):
	_MINIMAL_STRING_CONNECTOR = '; '

	_BORDER_COLOR = _ALL_COLOR
	_BORDER_TRIANGLE_COLOR = _ANY_COLOR


class AnyNode(BorderedNode):
	_MINIMAL_STRING_CONNECTOR = ' || '

	_BORDER_COLOR = _ANY_COLOR
	_BORDER_TRIANGLE_COLOR = _ALL_COLOR
