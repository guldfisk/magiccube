import copy
import itertools
import random
import typing as t

from magiccube.collections.laps import TrapCollection
from magiccube.laps.traps.trap import Trap
from yeetlong.multiset import FrozenMultiset

from evolution import model
from magiccube.laps.traps.distribute.algorithm import TrapDistribution, DistributionNode, TrapCollectionIndividual


class DistributionDelta(TrapCollectionIndividual):

    def __init__(
        self,
        origin: TrapDistribution,
        added_nodes: t.Collection[DistributionNode],
        removed_node_indexes: t.FrozenSet[int],
        max_trap_difference: int,
        trap_amount_delta: int = 0,
    ):
        super().__init__()

        self._origin = origin
        self._added_nodes = added_nodes
        self._removed_node_indexes = removed_node_indexes
        self._max_trap_difference = max_trap_difference

        self.node_moves: t.Dict[t.Tuple[int, int], int] = {}
        self.added_node_indexes: t.Dict[DistributionNode, int] = {}

        self._trap_amount_delta = trap_amount_delta

        self._all_index_set = frozenset(range(self.trap_amount))

        self.removed_trap_redistributions: t.Dict[int, t.List[int]] = {}

        for _ in range(self.removed_trap_amount):
            removed_index = self.get_available_trap_index()
            self.removed_trap_redistributions[removed_index] = []

        for removed_index in self.removed_trap_redistributions:
            for _ in self._origin.traps[removed_index]:
                self.removed_trap_redistributions[removed_index].append(
                    self.get_available_trap_index()
                )

        for index in itertools.chain(*self.removed_trap_redistributions.values()):
            if index in self.removed_trap_redistributions:
                raise Exception('dude what')

        for node in self._added_nodes:
            self.added_node_indexes[node] = random.sample(
                (
                    self.valid_trap_indexes
                    if len(self.modified_trap_indexes) < self._max_trap_difference else
                    self.modified_trap_indexes - self.removed_trap_redistributions.keys()
                ),
                1,
            )[0]

    @property
    def origin(self) -> TrapDistribution:
        return self._origin

    @property
    def trap_amount(self) -> int:
        return self._origin.trap_amount + self._trap_amount_delta

    @property
    def added_trap_amount(self) -> int:
        return max(self._trap_amount_delta, 0)

    @property
    def removed_trap_amount(self) -> int:
        return max(-self._trap_amount_delta, 0)

    @property
    def max_trap_difference(self) -> int:
        return self._max_trap_difference

    @property
    def removed_node_indexes(self) -> t.FrozenSet[int]:
        return self._removed_node_indexes

    @property
    def valid_trap_indexes(self) -> t.FrozenSet[int]:
        return self._all_index_set - self.removed_trap_redistributions.keys()

    def get_available_trap_index(self) -> int:
        modifications = self.modified_trap_indexes
        return random.sample(
            (
                self.valid_trap_indexes
                if len(modifications) < self.max_trap_difference else
                modifications - self.removed_trap_redistributions.keys()
            ),
            1
        )[0]

    def evacuate_removed_trap(self, index: int) -> None:
        for from_indexes, to_index in self.node_moves.items():
            if to_index == index:
                self.node_moves[from_indexes] = self.get_available_trap_index()

        changes: t.List[t.Tuple[int, int]] = []

        for indexes in self.node_moves:
            if indexes[0] == index:
                changes.append(indexes)

        for indexes in changes:
            del self.node_moves[indexes]

        for node, added_node_index in self.added_node_indexes.items():
            if index == added_node_index:
                self.added_node_indexes[node] = self.get_available_trap_index()

        for removed_index, target_indexes in self.removed_trap_redistributions.items():
            if not removed_index == index:
                continue

            for target_index_index, target_index in enumerate(target_indexes):
                if target_index in self.removed_trap_redistributions:
                    target_indexes[target_index_index] = self.get_available_trap_index()

    @property
    def modified_trap_indexes(self) -> t.FrozenSet[int]:
        return frozenset(
            itertools.chain(
                self._removed_node_indexes,
                (index for index, _ in self.node_moves),
                self.node_moves.values(),
                self.added_node_indexes.values(),
                range(self.origin.trap_amount, self.origin.trap_amount + self._trap_amount_delta),
                *self.removed_trap_redistributions.values(),
            )
        ) - self.removed_trap_redistributions.keys()

    @property
    def trap_distribution(self) -> TrapDistribution:
        modified_distribution = copy.deepcopy(self._origin)

        for _ in range(self.added_trap_amount):
            modified_distribution.traps.append([])

        moves: t.List[t.Tuple[DistributionNode, int]] = []

        for index, trap in enumerate(modified_distribution.traps):
            for from_indexes, to_index in sorted(
                (item for item in self.node_moves.items() if item[0][0] == index),
                key = lambda vs: vs[0][1],
                reverse = True,
            ):
                moves.append(
                    (
                        trap.pop(from_indexes[1]),
                        to_index,
                    )
                )

        for node, index in moves:
            modified_distribution.traps[index].append(node)

        for node, index in self.added_node_indexes.items():
            modified_distribution.traps[index].append(node)

        for from_index, target_indexes in self.removed_trap_redistributions.items():
            for target_index in target_indexes:
                modified_distribution.traps[target_index].append(
                    modified_distribution.traps[from_index].pop(0)
                )

        for index in sorted(self.removed_trap_redistributions, reverse=True):
            del modified_distribution.traps[index]

        return modified_distribution

    def as_trap_collection(self, *, intention_type: Trap.IntentionType = Trap.IntentionType.GARBAGE) -> TrapCollection:
        return self.trap_distribution.as_trap_collection()

    # def as_trap_collection(self) -> TrapCollection:
    #     return self.trap_distribution.as_trap_collection()


def mutate_distribution_delta(delta: DistributionDelta) -> t.Tuple[DistributionDelta]:
    for i in range(5):

        if random.random() < .8:
            modified_indexes = delta.modified_trap_indexes

            from_trap_index = random.sample(
                (
                    delta.valid_trap_indexes
                    if len(modified_indexes) < delta.max_trap_difference else
                    modified_indexes - delta.removed_trap_redistributions.keys()
                ),
                1
            )[0]

            node_index_options = frozenset(
                range(
                    len(
                        delta.origin.traps[from_trap_index]
                    )
                ) if from_trap_index < len(delta.origin.traps) else
                ()
            ) - frozenset(
                _node_index
                for _trap_index, _node_index in
                delta.node_moves
                if _trap_index == from_trap_index
            )

            if not node_index_options:
                continue

            node_index = random.sample(node_index_options, 1)[0]

            from_trap_index_set = frozenset((from_trap_index,))

            possible_trap_indexes_to = (
                modified_indexes - delta.removed_trap_redistributions.keys() - from_trap_index_set
                if len(modified_indexes | from_trap_index_set) >= delta.max_trap_difference else
                delta.valid_trap_indexes - from_trap_index_set
            )

            if not possible_trap_indexes_to:
                continue

            delta.node_moves[(from_trap_index, node_index)] = random.sample(possible_trap_indexes_to, 1)[0]

        else:

            if not delta.node_moves:
                continue

            del delta.node_moves[random.choice(list(delta.node_moves))]

    if delta.added_node_indexes:
        for i in range(2):

            if random.random() < .2:
                moved_node = random.choice(list(delta.added_node_indexes))
                from_trap_index = delta.added_node_indexes[moved_node]

                del delta.added_node_indexes[moved_node]

                modified_indexes = delta.modified_trap_indexes

                from_trap_index_set = frozenset((from_trap_index,))

                possible_trap_indexes_to = (
                    modified_indexes - delta.removed_trap_redistributions.keys() - from_trap_index_set
                    if len(modified_indexes) >= delta.max_trap_difference else
                    delta.valid_trap_indexes - from_trap_index_set
                )

                if not possible_trap_indexes_to:
                    continue

                delta.added_node_indexes[moved_node] = random.sample(possible_trap_indexes_to, 1)[0]

    if delta.removed_trap_redistributions:
        for _ in range(2):
            if random.random() < .05:
                unremoved_index = random.choice(list(delta.removed_trap_redistributions))

                new_removed_index = random.sample(delta.valid_trap_indexes, 1)[0]

                del delta.removed_trap_redistributions[unremoved_index]
                delta.removed_trap_redistributions[new_removed_index] = []

                delta.removed_trap_redistributions[new_removed_index] = [
                    delta.get_available_trap_index()
                    for _ in delta.origin.traps[new_removed_index]
                ]

                for index in delta.removed_trap_redistributions:
                    delta.evacuate_removed_trap(index)

        for _ in range(5):
            if random.random() < .1:
                trap = delta.removed_trap_redistributions[
                    random.choice(list(delta.removed_trap_redistributions))
                ]
                trap[random.randint(0, len(trap) - 1)] = delta.get_available_trap_index()

    return delta,


def mate_distribution_deltas(
    delta_1: DistributionDelta,
    delta_2: DistributionDelta,
) -> t.Tuple[DistributionDelta, DistributionDelta]:

    moves = copy.copy(delta_1.node_moves)
    moves.update(delta_2.node_moves)

    adds = {
        node:
            frozenset(
                (
                    delta_1.added_node_indexes[node],
                    delta_2.added_node_indexes[node],
                )
            )
        for node in
        delta_1.added_node_indexes
    }

    move_amounts = (len(delta_1.node_moves), len(delta_2.node_moves))
    min_moves = min(move_amounts)
    max_moves = max(move_amounts)

    removed_distributions: t.Dict[int, t.List[t.List[int]]] = {}

    deltas = (delta_1, delta_2)

    for delta in deltas:
        for index, indexes in delta.removed_trap_redistributions.items():
            try:
                removed_distributions[index].append(indexes)
            except KeyError:
                removed_distributions[index] = [indexes]


    for delta in deltas:

        modified = set()
        modified.update(delta.removed_node_indexes)

        delta.removed_trap_redistributions = {}
        for index, distribution_options in random.sample(removed_distributions.items(), delta.removed_trap_amount):
            delta.removed_trap_redistributions[index] = []
            modified.add(index)

            for options in zip(*distribution_options):
                if len(modified) < delta.max_trap_difference:
                    target_index = random.choice(options)
                    delta.removed_trap_redistributions[index].append(target_index)
                    modified.add(target_index)

                else:
                    moved = False
                    options = list(options)
                    random.shuffle(options)
                    for target_index in options:
                        if target_index in modified:
                            delta.removed_trap_redistributions[index].append(target_index)
                            moved = True
                            break

                    if not moved:
                        delta.removed_trap_redistributions[index].append(
                            random.sample(
                                delta.valid_trap_indexes & modified,
                                1
                            )[0]
                        )

        node_moves = {}

        for from_indexes, to_index in random.sample(moves.items(), random.randint(min_moves, max_moves)):
            if len(modified) >= delta.max_trap_difference:
                break

            if len(modified | {from_indexes[0], to_index}) > delta.max_trap_difference:
                continue

            node_moves[from_indexes] = to_index
            modified.add(from_indexes[0])
            modified.add(to_index)

        delta.node_moves = node_moves

        added_nodes = {}

        for added_node in delta.added_node_indexes:
            possible_indexes = adds[added_node]

            if len(modified) >= delta.max_trap_difference:
                possible_indexes -= modified

                if not possible_indexes:
                    possible_indexes = modified

            index = random.sample(possible_indexes, 1)[0]
            added_nodes[added_node] = index
            modified.add(index)

        for index in delta.removed_trap_redistributions:
            delta.evacuate_removed_trap(index)

    return delta_1, delta_2






# class DeltaDistributor(Distributor):
#
#     def __init__(
#         self,
#         constrained_nodes: t.Iterable[ConstrainedNode],
#         origin_trap_collection: t.Collection[Trap],
#         constraint_set_blue_print: ConstraintSetBluePrint,
#         max_trap_delta: int,
#         trap_amount: t.Optional[int] = None,
#         mate_chance: float = .5,
#         mutate_chance: float = .2,
#         tournament_size: int = 3,
#         population_size: int = 300,
#     ):
#         self._origin_trap_collection = origin_trap_collection
#         self._max_trap_delta = max_trap_delta
#
#         distribution, added, removed = self.trap_collection_to_trap_distribution(
#             self._origin_trap_collection,
#             constrained_nodes,
#         )
#
#         self._origin_trap_distribution = distribution
#         self._added = added
#         self._removed_trap_indexes = frozenset(
#             index
#             for node, index in
#             removed
#         )
#
#         super().__init__(
#             constrained_nodes,
#             (
#                 len(origin_trap_collection)
#                 if trap_amount is None else
#                 trap_amount
#             ),
#             constraint_set_blue_print,
#             mate_chance,
#             mutate_chance,
#             tournament_size,
#             population_size,
#         )
#
#     def _initialize_toolbox(self, toolbox: base.Toolbox):
#         toolbox.register(
#             'individual',
#             DistributionDelta,
#             origin = self._origin_trap_distribution,
#             added_nodes = self._added,
#             removed_node_indexes = self._removed_trap_indexes,
#             max_trap_difference = self._max_trap_delta,
#             trap_amount_delta = self.trap_amount - self._origin_trap_distribution.trap_amount,
#         )
#
#         toolbox.register('evaluate', lambda d: self._constraint_set.score(d.trap_distribution))
#         toolbox.register('mate', mate_distribution_deltas)
#         toolbox.register('mutate', mutate_distribution_delta)

