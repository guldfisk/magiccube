import typing as t

import os
from enum import Enum

from PIL import Image

from mtgorp.models.serilization.serializeable import serialization_model, Inflator
from mtgorp.models.persistent.printing import Printing
from mtgimg.interface import ImageLoader

from magiccube import paths
from magiccube.laps.lap import Lap
from magiccube.laps.traps.tree.printingtree import BorderedNode
from magiccube.laps import imageutils


class IntentionType(Enum):
	SYNERGY = 'synergy'
	OR = 'or'
	GARBAGE = 'garbage'
	LAND_GARBAGE = 'land_garbage'
	NO_INTENTION = 'no_intention'


class Trap(Lap):

	def __init__(self, node: BorderedNode, intention_type: IntentionType = IntentionType.NO_INTENTION):
		self._node = node
		self._intention_type = intention_type

	@property
	def node(self) -> BorderedNode:
		return self._node

	@property
	def intention_type(self) -> t.Optional[IntentionType]:
		return self._intention_type

	def serialize(self) -> serialization_model:
		return {
			'node': self._node.serialize(),
			'intention_type': self._intention_type.name,
		}

	@classmethod
	def deserialize(cls, value: serialization_model, inflator: Inflator) -> 'Trap':
		if not 'node' in value:
			return cls(
				BorderedNode.deserialize(
					value,
					inflator,
				),
			)
		return cls(
			BorderedNode.deserialize(
				value['node'],
				inflator,
			),
			IntentionType[value['intention_type']] if 'intention_type' in value else None,
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
			triangled = False,
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

	@classmethod
	def get_image_dir_name(cls) -> str:
		return 'cube_traps'

	def has_back(self) -> bool:
		return False

	def __hash__(self):
		return hash(self._node)

	def persistent_hash(self) -> str:
		return self._node.persistent_hash()

	def __eq__(self, other):
		return (
			isinstance(other, self.__class__)
			and self._node == other._node
		)

	def __iter__(self) -> t.Iterable[Printing]:
		return self._node.__iter__()

	def __contains__(self, item):
		return item in self.__iter__()

	def __repr__(self) -> str:
		return f'{self.__class__.__name__}({self._intention_type.value}, {self._node})'
