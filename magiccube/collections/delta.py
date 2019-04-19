
from mtgorp.utilities.containers import HashableMultiset
from mtgorp.models.persistent.printing import Printing

from magiccube.collections.cube import Cube


class CubeDelta(object):
	
	def __init__(self, original: Cube, current: Cube):
		self._original = original
		self._current = current
		
		self._new_pickables = None
		self._removed_pickables = None
		self._new_printings = None
		self._removed_printings = None

	@property
	def new_pickables(self) -> Cube:
		if self._new_pickables is None:
			self._new_pickables = self._current - self._original
		
		return self._new_pickables

	@property
	def removed_pickables(self) -> Cube:
		if self._removed_pickables is None:
			self._removed_pickables = self._original - self._current

		return self._removed_pickables
	
	@property
	def new_printings(self) -> HashableMultiset[Printing]:
		if self._new_printings is None:
			self._new_printings = (
				HashableMultiset(self._current.all_printings)
				- HashableMultiset(self._original.all_printings)
			)

		return self._new_printings

	@property
	def removed_printings(self) -> HashableMultiset[Printing]:
		if self._removed_printings is None:
			self._removed_printings = (
				HashableMultiset(self._original.all_printings)
				- HashableMultiset(self._current.all_printings)
			)

		return self._removed_printings

	@staticmethod
	def _multiset_to_indented_string(ms: HashableMultiset[Printing]) -> str:
		return '\n'.join(
			f'\t{multiplicity}x {printing}'
			for printing, multiplicity in
			sorted(
				ms.items(),
				key=lambda item: str(item[0])
			)
		)

	@property
	def report(self) -> str:
		return f'New pickables:\n{self.new_pickables.pp_string}\n------\n' \
			   f'Removed pickables:\n{self.removed_pickables.pp_string}\n------\n' \
			   f'New printings ({len(self.new_printings)}):\n' \
			   f'{self._multiset_to_indented_string(self.new_printings)}\n' \
			   f'Removed printings ({len(self.removed_printings)}):\n' \
			   f'{self._multiset_to_indented_string(self.removed_printings)}'
