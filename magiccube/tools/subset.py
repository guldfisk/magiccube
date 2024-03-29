import itertools
import typing as t
from collections import defaultdict

from mtgorp.models.interfaces import Cardboard, Printing
from yeetlong.errors import Errors
from yeetlong.multiset import BaseMultiset, FrozenMultiset, Multiset

from magiccube.collections.cube import Cube
from magiccube.laps.traps.tree.printingtree import AnyNode, NodeAny


def _amount_printing_to_required_tickets(amount: int) -> int:
    return int((amount + 1) * amount / 2)


def check_deck_subset_pool(
    pool: Cube,
    deck: BaseMultiset[Printing],
    exempt_cardboards: t.AbstractSet[Cardboard] = frozenset(),
    *,
    strict: bool = True,
) -> Errors:
    """
    I am to lazy to make this work properly for cases that aren't required yet.
    This does not work properly if copies of the same printing are present in both tickets and traps.
    This also does not work properly if tickets have overlap (although it is not even really well defined how this
    should work)
    """

    if not strict:
        pool = pool.as_cardboards
        deck = FrozenMultiset(p.cardboard for p in deck)

    printings = Multiset(pool.models)
    anys: Multiset[AnyNode] = Multiset()

    for child in itertools.chain(*(trap.node.flattened for trap in pool.traps)):
        if isinstance(child, NodeAny):
            anys.add(child)
        else:
            printings.add(child)

    ticket_printings = set(itertools.chain(*pool.tickets))

    unaccounted_printings = (
        Multiset(
            {
                printing: multiplicity
                for printing, multiplicity in deck.items()
                if ((printing.cardboard not in exempt_cardboards) if strict else (printing not in exempt_cardboards))
            }
        )
        - printings
    )

    printings_in_tickets = Multiset()
    printing_to_anys = defaultdict(list)

    flattened_anys = {_any: FrozenMultiset(_any.flattened_options) for _any in anys.distinct_elements()}

    for _any, options in flattened_anys.items():
        for option in options:
            for printing in option:
                printing_to_anys[printing].append(_any)

    any_potential_option_uses = defaultdict(Multiset)

    for unaccounted_printing in unaccounted_printings:
        _anys = printing_to_anys.get(unaccounted_printing)

        if not _anys:
            if unaccounted_printing in ticket_printings:
                printings_in_tickets.add(unaccounted_printing)
                continue
            return Errors([f"Pool does not contain {unaccounted_printing}"])

        for _any in _anys:
            for option in flattened_anys[_any]:
                if unaccounted_printing in option:
                    any_potential_option_uses[_any].add(option)

    uncontested_options = Multiset()
    contested_options = []
    for _any, options in any_potential_option_uses.items():
        for _ in range(anys.elements().get(_any, 0)):
            if not options:
                continue
            if len(options) == 1:
                uncontested_options.update(options.__iter__().__next__())
            else:
                contested_options.append(flattened_anys[_any])

    contested_printings = Multiset(
        printing for printing in unaccounted_printings - uncontested_options if printing not in printings_in_tickets
    )

    combination_printings = Multiset()
    if contested_options:
        solution_found = False
        for combination in itertools.product(*contested_options):
            combination_printings = Multiset(itertools.chain(*combination))
            if contested_printings <= combination_printings:
                solution_found = True
                break
    else:
        solution_found = True

    if not solution_found:
        return Errors(["No suitable combination of any choices"])

    unaccounted_printings -= combination_printings + uncontested_options

    if not unaccounted_printings:
        return Errors()

    printings_to_tickets = defaultdict(set)

    for ticket in pool.tickets:
        for printing in ticket:
            printings_to_tickets[printing].add(ticket)

    tickets_to_printings = defaultdict(list)

    for printing, multiplicity in unaccounted_printings.items():
        for ticket in printings_to_tickets[printing]:
            tickets_to_printings[ticket].append(printing)

    uncontested_tickets = []
    contested_tickets_printings = []
    contested_tickets_tickets = []

    for ticket, printings in tickets_to_printings.items():
        if len(printings) == 1:
            uncontested_tickets.append((ticket, printings[0]))
        else:
            contested_tickets_printings.append(printings)
            contested_tickets_tickets.append(ticket)

    for ticket, printing in uncontested_tickets:
        if _amount_printing_to_required_tickets(unaccounted_printings[printing]) > pool.tickets[ticket]:
            return Errors([f"Not enough tickets to pay for {printing}"])

    if contested_tickets_printings:
        solution_found = False
        for combination in itertools.product(*contested_tickets_printings):
            _printings_to_tickets = defaultdict(list)

            for ticket, printing in zip(contested_tickets_tickets, combination):
                _printings_to_tickets[printing].append(ticket)

            for printing, tickets in _printings_to_tickets.items():
                if _amount_printing_to_required_tickets(unaccounted_printings[printing]) <= sum(
                    pool.tickets[ticket] for ticket in tickets
                ):
                    solution_found = True
                    break

            if solution_found:
                break
    else:
        solution_found = True

    if not solution_found:
        return Errors(["No suitable combination of tickets"])

    return Errors()
