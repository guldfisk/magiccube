import typing as t
from collections import Counter

from mtgorp.models.persistent.printing import Printing
from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator
from mtgorp.utilities.containers import HashableMultiset

from magiccube.collections.cube import Cube
from magiccube.laps.purples.purple import Purple
from magiccube.laps.tickets.ticket import Ticket
from magiccube.laps.traps.trap import Trap


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


class CubeDeltaOperation(Serializeable):

    def __init__(
        self,
        printings: t.Optional[t.Mapping[Printing, int]] = None,
        traps: t.Optional[t.Mapping[Trap, int]] = None,
        tickets: t.Optional[t.Mapping[Ticket, int]] = None,
        purples: t.Optional[t.Mapping[Purple, int]] = None,
    ):
        self._printings = Counter() if printings is None else Counter(printings)
        self._traps = Counter() if traps is None else Counter(traps)
        self._tickets = Counter() if tickets is None else Counter(tickets)
        self._purples = Counter() if purples is None else Counter(purples)

    @property
    def printings(self) -> t.Iterable[Printing]:
        return self._printings

    @property
    def traps(self) -> t.Iterable[Trap]:
        return self._traps

    @property
    def tickets(self) -> t.Iterable[Ticket]:
        return self._tickets

    @property
    def purples(self) -> t.Iterable[Purple]:
        return self._purples

    def serialize(self) -> serialization_model:
        return {
            'printings': self._printings.items(),
            'traps': self._traps.items(),
            'tickets': self._tickets.items(),
            'purples': self._purples.items(),
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> 'Serializeable':
        return cls(
            printings = {
                inflator.inflate(Printing, printing): multiplicity
                for printing, multiplicity in
                value['printings']
            },
            traps = {
                Trap.deserialize(trap, inflator): multiplicity
                for trap, multiplicity in
                value.get('traps', ())
            },
            tickets = {
                Ticket.deserialize(ticket, inflator): multiplicity
                for ticket, multiplicity in
                value.get('tickets', ())
            },
            purples = {
                Purple.deserialize(purple, inflator): multiplicity
                for purple, multiplicity in
                value.get('purples', ())
            }
        )

    def __hash__(self) -> int:
        return hash((self._printings, self._traps, self._tickets, self._purples))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._printings == other._printings
            and self._traps == other._traps
            and self._tickets == other._tickets
            and self._purples == other._purples
        )

    def __repr__(self) -> str:
        return '{}({}, {}, {}, {})'.format(
            self.__class__.__name__,
            self._printings,
            self._traps,
            self._tickets,
            self._purples,
        )