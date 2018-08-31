import typing as t

import os

from PIL import Image

from mtgorp.models.serilization.serializeable import serialization_model, Inflator
from mtgorp.models.persistent.printing import Printing
from mtgimg.interface import ImageLoader

from magiccube import paths
from magiccube.laps.lap import Lap
from magiccube.laps.traps.tree.printingtree import BorderedNode
from magiccube.laps import imageutils


class Trap(Lap):

	def __init__(self, node: BorderedNode):
		self._node = node

	def serialize(self) -> serialization_model:
		return self._node.serialize()

	@classmethod
	def deserialize(cls, value: serialization_model, inflator: Inflator) -> 'Trap':
		return cls(
			BorderedNode.deserialize(
				value,
				inflator,
			)
		)

	def get_image(
		self,
		size: t.Tuple[int, int],
		loader: 'ImageLoader',
		back: bool = False,
		crop: bool = False,
	) -> Image.Image:

		image = self._node.get_image(
			loader = loader,
			width = 560,
			height = 435 if crop else 784,
			bordered_sides = imageutils.HORIZONTAL_SIDES,
		)

		if crop:
			return image

		return Image.composite(
			image,
			Image.new('RGBA', (560, 784), (0, 0, 0, 0)),
			Image.open(
				os.path.join(
					paths.IMAGES_PATH,
					'mask.png',
				)
			)
		)

	def get_image_name(self, back: bool = False, crop: bool = False) -> str:
		return self._node.persistent_hash()

	def get_image_dir_name(self) -> str:
		return 'cube_traps'

	def has_back(self) -> bool:
		return False

	def __hash__(self):
		return hash(self._node)

	def __eq__(self, other):
		return (
			isinstance(other, self.__class__)
			and self._node == other._node
		)

	def __iter__(self) -> t.Iterable[Printing]:
		return self._node.__iter__()

	def __repr__(self) -> str:
		return f'{self.__class__.__name__}({self._node})'
