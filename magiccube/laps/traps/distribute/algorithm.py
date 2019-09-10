from __future__ import annotations

import typing as t

import math
import random
import itertools
from collections import OrderedDict

import matplotlib.pyplot as plt

from evolution import logging, model
from evolution.environment import Environment
from magiccube.collections.laps import TrapCollection

from yeetlong.multiset import FrozenMultiset

from magiccube.laps.traps.tree.printingtree import AllNode, PrintingNode
from magiccube.laps.traps.trap import Trap, IntentionType
from magiccube.collections.nodecollection import ConstrainedNode


class DistributionNode(object):
    
    def __init__(self, node: ConstrainedNode):
        self._value = node.value
        self._node = node.node
        self._groups = frozenset(group for group in node.groups if group)

    @property
    def value(self) -> float:
        return self._value

    @property
    def node(self) -> PrintingNode:
        return self._node

    @property
    def groups(self) -> t.FrozenSet[str]:
        return self._groups

    @property
    def as_constrained_node(self):
        return ConstrainedNode(
            value = self._value,
            node = self._node,
            groups = self._groups,
        )
  
    def __repr__(self):
        return f'DN({self.node}, {self.groups}, {self.value})'

    def __deepcopy__(self, memodict: t.Dict):
        return self


class TrapDistribution(model.Individual):

    def __init__(
        self,
        distribution_nodes: t.Iterable[DistributionNode] = (),
        trap_amount: int = 1,
        traps: t.Optional[t.List[t.List[DistributionNode]]] = None,
        random_initialization: bool = False
    ):
        super().__init__()

        self._trap_amount = trap_amount

        if traps is None:
            self.traps: t.List[t.List[DistributionNode]] = [[] for _ in range(trap_amount)]

            if random_initialization:
                for constrained_node in distribution_nodes:
                    random.choice(self.traps).append(constrained_node)

            else:
                for constrained_node, trap in zip(
                    distribution_nodes,
                    itertools.cycle(self.traps)
                ):
                    trap.append(constrained_node)

        else:
            self.traps = traps #type: t.List[t.List[DistributionNode]]
            self._trap_amount = len(self.traps)

    @property
    def trap_amount(self):
        return self._trap_amount

    def as_trap_collection(self, *, intention_type: IntentionType = IntentionType.GARBAGE) -> TrapCollection:
        traps = []

        for trap in self.traps:
            cubeables = []

            if not trap:
                raise Exception('Empty trap')

            for constrained_node in trap:
                cubeable = constrained_node.node
                if isinstance(cubeable, AllNode) and len(cubeable.children) == 1:
                    cubeables.extend(cubeable.children)
                else:
                    cubeables.append(cubeable)

            traps.append(
                Trap(
                    AllNode(cubeables),
                    intention_type = intention_type,
                )
            )

        return TrapCollection(traps)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.traps})'


def mutate_trap_distribution(distribution: TrapDistribution, distributor: Distributor) -> TrapDistribution:
    for i in range(3):
        selected_group = random.choice(
            [
                group
                for group in
                distribution.traps
                if group
            ]
        )
        target_group = random.choice(
            [
                group
                for group in
                distribution.traps
                if group != selected_group
            ]
        )
        target_group.append(
            selected_group.pop(
                random.randint(
                    0,
                    len(selected_group) - 1,
                )
            )
        )

    return distribution


def mate_distributions(
    distribution_1: TrapDistribution,
    distribution_2: TrapDistribution,
    distributor: 'Distributor',
) -> t.Tuple[TrapDistribution, TrapDistribution]:

    locations = {
        node: []
        for node in
        distributor.distribution_nodes
    }

    for distribution in (distribution_1, distribution_2):
        for i, traps in enumerate(distribution.traps):
            for node in traps:
                locations[node].append(i)

    for distribution in (distribution_1, distribution_2):
        traps = [
            []
            for _ in
            range(distributor.trap_amount)
        ]

        for node, possibilities in locations.items():
            traps[random.choice(possibilities)].append(node)

        distribution.traps = traps

    return distribution_1, distribution_2



def logistic(x: float, max_value: float, mid: float, slope: float) -> float:
    try:
        return max_value / (1 + math.e ** (slope * (x - mid)))
    except OverflowError:
        return 0


class ValueDistributionHomogeneityConstraint(model.Constraint):
    description = 'Value distribution homogeneity'

    def __init__(
        self,
        nodes: t.Iterable[DistributionNode],
        trap_amount: int,
    ):
        self._average_trap_value = (
            sum(
                (
                    node.value
                    for node in
                    nodes
                )
            ) / trap_amount
        )
        self._relator = self._average_trap_value ** 2 * trap_amount

    def _value_distribution_heterogeneity_factor(self, distribution: TrapDistribution) -> float:
        return sum(
            (
                (
                    sum(
                        node.value
                        for node in
                        trap
                    ) - self._average_trap_value
                ) ** 2
                for trap in
                distribution.traps
            )
        )

    def score(self, distribution: TrapDistribution) -> float:
        return logistic(
            x = self._value_distribution_heterogeneity_factor(
                distribution
            ) / self._relator,
            max_value = 2,
            mid = 0,
            slope = 7,
        )


class GroupExclusivityConstraint(model.Constraint):
    description = 'Group exclusivity'

    def __init__(
        self,
        nodes: t.Iterable[DistributionNode],
        trap_amount: int,
        group_weights: t. Mapping[str, float],
    ):
        self._group_weights = {} if group_weights is None else group_weights

        self._relator = (
            self._get_nodes_collision_factor(
                nodes
            ) / trap_amount
        ) ** 2

    def _get_nodes_collision_factor(self, nodes: t.Iterable[DistributionNode]) -> float:
        groups = {}  # type: t.Dict[str, t.List[DistributionNode]]
        collisions = {}  # type: t.Dict[t.FrozenSet[DistributionNode], t.List[str]]

        for constrained_node in nodes:
            for group in constrained_node.groups:

                if group in groups:
                    for other_node in groups[group]:
                        _collision_key = frozenset((constrained_node, other_node))
                        try:
                            collisions[_collision_key].append(group)
                        except KeyError:
                            collisions[_collision_key] = [group]

                    groups[group].append(constrained_node)

                else:
                    groups[group] = [constrained_node]

        return sum(
            (
                1 - 1 / (1 + sum(node.value for node in nodes))
                * max(self._group_weights.get(group, .1) for group in groups)
            )
            for nodes, groups in
            collisions.items()
        )
        
    def _group_collision_factor(self, distribution: TrapDistribution) -> int:
        return sum(
            self._get_nodes_collision_factor(trap) ** 2
            for trap in
            distribution.traps
        )

    def score(self, distribution: TrapDistribution) -> float:
        return logistic(
            x = self._group_collision_factor(
                distribution
            ) / self._relator,
            max_value = 2,
            mid = 0,
            slope = 8,
        )


class SizeHomogeneityConstraint(model.Constraint):
    description = 'Size homogeneity'

    def __init__(
        self,
        nodes: t.List[DistributionNode],
        trap_amount: int,
    ):
        self._average_trap_size = len(nodes) / trap_amount
        self._relator = self._average_trap_size ** 2 * trap_amount

    def _size_heterogeneity_factor(self, distribution: TrapDistribution) -> float:
        return sum(
            (
                len(trap) - self._average_trap_size
            ) ** 2
            for trap in
            distribution.traps
        )

    def score(self, distribution: TrapDistribution) -> float:
        return logistic(
            x = self._size_heterogeneity_factor(
                distribution
            ) / self._relator,
            max_value = 2,
            mid = 0,
            slope = 5,
        )


class Distributor(Environment[TrapDistribution]):

    def __init__(
        self,
        nodes: t.Iterable[ConstrainedNode],
        trap_amount: int,
        initial_population_size: int,
        constraints: model.ConstraintSet,
        **kwargs,
    ):
        self._distribution_nodes: t.List[DistributionNode] = list(
            map(
                DistributionNode,
                nodes,
            )
        )
        self._trap_amount = trap_amount

        super().__init__(
            individual_factory = (
                lambda:
                    TrapDistribution(
                        distribution_nodes = self._distribution_nodes,
                        trap_amount = self._trap_amount,
                        random_initialization = True,
                    )
            ),
            initial_population_size = initial_population_size,
            constraints = constraints,
            logger = logging.Logger(
                OrderedDict(
                    (
                        (
                            'max',
                            logging.LogMax(),
                        ),
                        (
                            'mean',
                            logging.LogAverage(),
                        ),
                    )
                )
            ),
            mutate = mutate_trap_distribution,
            mate = mate_distributions,
            **kwargs,
        )

    @property
    def distribution_nodes(self) -> t.List[DistributionNode]:
        return self._distribution_nodes

    @property
    def trap_amount(self):
        return self._trap_amount

    def show_plot(self) -> None:
        generations = range(len(self._logger.values))
        fit_maxes = [frame[0] for frame in self._logger.values]
        fit_averages = [frame[1] for frame in self._logger.values]

        fig, ax1 = plt.subplots()

        colors = ('r', 'g', 'b', 'c', 'm', 'y')

        # lines = functools.reduce(
        #     operator.add,
        #     (
        #         ax1.plot(
        #             generations,
        #             self._logbook.select(constraint.description),
        #             color,
        #             label=f'Max {constraint.description} score',
        #         )
        #         for constraint, color in
        #         zip(self._constraint_set, colors)
        #     ),
        # )

        # ax2 = ax1.twinx()

        max_line = ax1.plot(generations, fit_maxes, 'k', label='Maximum Fitness')
        average_line = ax1.plot(generations, fit_averages, '.75', label='Average Fitness')

        lns = max_line + average_line
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc="lower right")

        plt.show()
        


# class _Distributor(object):
#
#     def __init__(
#         self,
#         constrained_nodes: t.Iterable[ConstrainedNode],
#         trap_amount: int,
#         constraint_set_blue_print: ConstraintSetBluePrint,
#         mate_chance: float = .5,
#         mutate_chance: float = .2,
#         tournament_size: int = 3,
#         population_size: int = 300,
#     ):
#         # TODO wtf is happening with these two
#         self._unique_constrained_nodes = frozenset(constrained_nodes)
#         self._constrained_nodes = FrozenMultiset(constrained_nodes)
#
#         self._trap_amount = trap_amount
#         self._constraint_set_blue_print = constraint_set_blue_print
#         self._mate_chance = mate_chance
#         self._mutate_chance = mutate_chance
#         self._tournament_size = tournament_size
#         self._population_size = population_size
#
#         self._toolbox = base.Toolbox()
#
#         self._initialize_toolbox(self._toolbox)
#
#         self._toolbox.register('population', tools.initRepeat, list, self._toolbox.individual)
#
#         self._population = self._toolbox.population(n=self._population_size) #type: t.List[TrapDistribution]
#
#         self._sample_random_population = [
#             TrapDistribution(self._unique_constrained_nodes, self._trap_amount, random_initialization=True)
#             for _ in
#             range(self._population_size)
#         ]
#
#         self._constraint_set = self._constraint_set_blue_print.realise(
#             self._unique_constrained_nodes,
#             self._trap_amount,
#             self._sample_random_population,
#         )
#
#         self._toolbox.register('select', tools.selTournament, tournsize=self._tournament_size)
#
#         self._best = None
#
#         self._statistics = tools.Statistics(key=lambda ind: ind)
#         self._statistics.register('avg', lambda s: statistics.mean(e.fitness.values[0] for e in s))
#         self._statistics.register('max', lambda s: max(e.fitness.values[0] for e in s))
#
#         class _MaxMap(object):
#
#             def __init__(self, _index: int):
#                 self._index = _index
#
#             def __call__(self, population: t.Collection[TrapDistribution]):
#                 return sorted(
#                     (
#                         individual
#                         for individual in
#                         population
#                     ),
#                     key = lambda individual:
#                         individual.fitness.values[0]
#                 )[-1].fitness.values[self._index]
#
#         for index, constraint in enumerate(self._constraint_set):
#             self._statistics.register(
#                 constraint.description,
#                 _MaxMap(index + 1),
#             )
#
#         self._logbook = None #type: tools.Logbook
#
#     def _initialize_toolbox(self, toolbox: base.Toolbox):
#         toolbox.register(
#             'individual',
#             TrapDistribution,
#             constrained_nodes = self._unique_constrained_nodes,
#             trap_amount = self._trap_amount,
#             random_initialization = True,
#         )
#
#         toolbox.register('evaluate', lambda d: self._constraint_set.score(d))
#         toolbox.register('mate', mate_distributions, distributor=self)
#         toolbox.register('mutate', mutate_trap_distribution)
#
#     @property
#     def population(self) -> t.List[TrapDistribution]:
#         return self._population
#
#     @property
#     def sample_random_population(self) -> t.List[TrapDistribution]:
#         return self._sample_random_population
#
#     @property
#     def best(self) -> TrapDistribution:
#         if self._best is None:
#             self._best = tools.selBest(self._population, 1)[0]
#
#         return self._best
#
#     @property
#     def constrained_nodes(self) -> t.FrozenSet[ConstrainedNode]:
#         return self._unique_constrained_nodes
#
#     @property
#     def trap_amount(self) -> int:
#         return self._trap_amount
#
#     @property
#     def constraint_set(self) -> ConstraintSet:
#         return self._constraint_set
#
#     @classmethod
#     def trap_collection_to_trap_distribution(
#         cls,
#         traps: t.Collection[Trap],
#         constrained_nodes: t.Iterable[ConstrainedNode],
#     ) -> t.Tuple[TrapDistribution, t.List[ConstrainedNode], t.List[t.Tuple[PrintingNode, int]]]:
#
#         constraint_map = {} #type: t.Dict[PrintingNode, t.List[ConstrainedNode]]
#
#         for constrained_node in constrained_nodes:
#             try:
#                 constraint_map[constrained_node.node].append(constrained_node)
#             except KeyError:
#                 constraint_map[constrained_node.node] = [constrained_node]
#
#         distribution = [[] for _ in range(len(traps))] #type: t.List[t.List[ConstrainedNode]]
#         removed = [] #type: t.List[t.Tuple[PrintingNode, int]]
#
#         for index, trap in enumerate(traps):
#
#             for child in trap.node.children:
#                 printing_node = child if isinstance(child, PrintingNode) else AllNode((child,))
#
#                 try:
#                     distribution[index].append(constraint_map[printing_node].pop())
#                 except (KeyError, IndexError):
#                     removed.append((printing_node, index))
#
#         added = list(
#             itertools.chain(
#                 *(
#                     nodes
#                     for nodes in
#                     constraint_map.values()
#                 )
#             )
#         )
#
#         return TrapDistribution(traps=distribution), added, removed
#
#     def evaluate_cube(self, traps: t.Collection[Trap]) -> float:
#         distribution, added, removed = self.trap_collection_to_trap_distribution(
#             traps,
#             self._constrained_nodes,
#         )
#         if added or removed:
#             raise ValueError(f'Collection does not match distribution. Added: "{added}", removed: "{removed}".')
#
#         return self._constraint_set.score(distribution)[0]
#
#     def show_plot(self) -> 'Distributor':
#         generations = self._logbook.select("gen")
#         fit_maxes = self._logbook.select('max')
#         fit_averages = self._logbook.select('avg')
#
#         fig, ax1 = plt.subplots()
#
#         colors = ('r', 'g', 'b', 'c', 'm', 'y')
#
#         lines = functools.reduce(
#             operator.add,
#             (
#                 ax1.plot(
#                     generations,
#                     self._logbook.select(constraint.description),
#                     color,
#                     label = f'Max {constraint.description} score',
#                 )
#                 for constraint, color in
#                 zip(self._constraint_set, colors)
#             ),
#         )
#
#         ax2 = ax1.twinx()
#
#         max_line = ax2.plot(generations, fit_maxes, 'k', label='Maximum Fitness')
#         average_line = ax2.plot(generations, fit_averages, '.75', label='Average Fitness')
#
#         lns = max_line + average_line + lines
#         labs = [l.get_label() for l in lns]
#         ax1.legend(lns, labs, loc="lower right")
#
#         plt.show()
#
#         return self
#
#     def evaluate(self, generations: int) -> 'Distributor':
#         population, logbook = algorithms.eaSimple(
#             self._population,
#             self._toolbox,
#             self._mate_chance,
#             self._mutate_chance,
#             generations,
#             stats = self._statistics,
#         )
#
#         self._population = population
#         self._logbook = logbook
#         self._best = None
#
#         return self

