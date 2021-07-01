from __future__ import annotations

import typing as t

import math
import random
import itertools
from abc import abstractmethod
from collections import OrderedDict

import matplotlib.pyplot as plt

from evolution import logging, model
from evolution import environment
from evolution.constraints import Constraint
from evolution.environment import Environment, EvolutionModelBlueprint, I

from mtgorp.models.interfaces import Printing

from magiccube.collections.laps import TrapCollection
from magiccube.laps.traps.tree.printingtree import AllNode, PrintingNode
from magiccube.laps.traps.trap import Trap, IntentionType
from magiccube.collections.nodecollection import ConstrainedNode


class DistributionNode(object):

    def __init__(self, node: ConstrainedNode, *, auto_add_color: bool = True):
        self._value = node.value
        self._node = node.node
        self._groups = frozenset(group for group in node.groups if group)
        if auto_add_color and len(self._node.children.distinct_elements()) == 1:
            child = self._node.children.__iter__().__next__()
            if isinstance(child, Printing) and len(child.cardboard.front_card.color) <= 2:
                self._groups |= frozenset(color.name for color in child.cardboard.front_card.color)

        self._image_amount = self.node.image_amount

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        self._value = value

    @property
    def node(self) -> PrintingNode:
        return self._node

    @property
    def groups(self) -> t.FrozenSet[str]:
        return self._groups

    @property
    def image_amount(self) -> int:
        return self._image_amount

    @property
    def as_constrained_node(self):
        return ConstrainedNode(
            value = self._value,
            node = self._node,
            groups = self._groups,
        )

    def __repr__(self):
        return f'DN({self.node}, {self.groups}, {self.value})'

    def __copy__(self):
        return self

    def __deepcopy__(self, memodict: t.Dict):
        return self


class TrapCollectionIndividual(model.Individual):
    class InvalidDistribution(Exception):
        pass

    @abstractmethod
    def as_trap_collection(
        self,
        *,
        intention_type: IntentionType = IntentionType.GARBAGE,
    ) -> TrapCollection:
        pass


T = t.TypeVar('T', bound = TrapCollectionIndividual)


class TrapDistribution(TrapCollectionIndividual):
    traps: t.List[t.List[DistributionNode]]

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
            self.traps = [[] for _ in range(trap_amount)]

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
            self.traps = traps
            self._trap_amount = len(self.traps)

    @property
    def trap_amount(self):
        return self._trap_amount

    def as_trap_collection(
        self,
        *,
        intention_type: IntentionType = IntentionType.GARBAGE,
    ) -> TrapCollection:
        traps = []

        for trap in self.traps:
            cubeables = []

            if not trap:
                raise self.InvalidDistribution('Empty trap')

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


def logistic(x: float, max_value: float, mid: float, slope: float) -> float:
    try:
        return max_value / (1 + math.e ** (slope * (x - mid)))
    except OverflowError:
        return 0


class ValueDistributionHomogeneityConstraint(Constraint):
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


class GroupExclusivityConstraint(Constraint):
    description = 'Group exclusivity'

    def __init__(
        self,
        nodes: t.Iterable[DistributionNode],
        trap_amount: int,
        group_weights: t.Mapping[str, float],
    ):
        self._group_weights = {} if group_weights is None else group_weights

        self._relator = (
                            self._get_nodes_collision_factor(
                                nodes
                            ) / trap_amount
                        ) ** 2

    def _get_nodes_collision_factor(self, nodes: t.Iterable[DistributionNode]) -> float:
        groups: t.Dict[str, t.List[DistributionNode]] = {}
        collisions: t.Dict[t.FrozenSet[DistributionNode], t.List[str]] = {}

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
                (1 - 1 / (1 + sum(node.value for node in nodes)))
                * max(self._group_weights.get(group, .1) for group in groups)
            )
                for nodes, groups in
                collisions.items()
        )

    def group_collision_factor(self, distribution: TrapDistribution) -> int:
        return sum(
            self._get_nodes_collision_factor(trap) ** 2
                for trap in
                distribution.traps
        )

    def score(self, distribution: TrapDistribution) -> float:
        return logistic(
            x = self.group_collision_factor(
                distribution
            ) / self._relator,
            max_value = 2,
            mid = 0,
            slope = 100,
        )


class SizeHomogeneityConstraint(Constraint):
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
            (len(trap) - self._average_trap_size) ** 2
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


class ImageAmountHomogeneity(Constraint):
    description = 'Image amount homogeneity'

    def __init__(
        self,
        nodes: t.List[DistributionNode],
        trap_amount: int,
    ):
        self._average_trap_image_amount = sum(node.image_amount for node in nodes) / trap_amount
        self._relator = self._average_trap_image_amount ** 2 * trap_amount

    def _image_amount_heterogeneity_factor(self, distribution: TrapDistribution) -> float:
        return sum(
            (sum(node.image_amount for node in trap) - self._average_trap_image_amount) ** 2
            for trap in
            distribution.traps
        )

    def score(self, distribution: TrapDistribution) -> float:
        return logistic(
            x = self._image_amount_heterogeneity_factor(
                distribution
            ) / self._relator,
            max_value = 2,
            mid = 0,
            slope = 5,
        )


class BaseDistributor(Environment[T]):

    def __init__(
        self,
        distribution_nodes: t.Iterable[DistributionNode],
        trap_amount: int,
        constraints: t.Callable[[I], t.Tuple[float, ...]],
        model_blue_print: t.Optional[EvolutionModelBlueprint] = None,
        logger: t.Optional[logging.Logger] = None,
        **kwargs,
    ):
        self._model_blue_print = (
            model_blue_print or
            EvolutionModelBlueprint(environment.SimpleModel, initial_population_size = 300)
        )
        self._distribution_nodes: t.List[DistributionNode] = list(distribution_nodes)
        self._trap_amount = trap_amount

        super().__init__(
            self._model_blue_print.realise(
                individual_factory = self.create_individual,
                fitness_evaluator = constraints,
                mutate = lambda i, d: self.mutate(i),
                mate = lambda f, s, d: self.mate(f, s),
            ),
            logger = logger or logging.Logger(
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
            **kwargs,
        )

    @abstractmethod
    def mutate(self, distribution: T) -> T:
        pass

    @abstractmethod
    def mate(self, first: T, second: T) -> t.Tuple[T, T]:
        pass

    @abstractmethod
    def create_individual(self) -> T:
        pass

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

        max_line = ax1.plot(generations, fit_maxes, 'k', label = 'Maximum Fitness')
        average_line = ax1.plot(generations, fit_averages, '.75', label = 'Average Fitness')

        lns = max_line + average_line
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc = "lower right")

        plt.show()


class Distributor(BaseDistributor[TrapDistribution]):

    def create_individual(self) -> TrapCollectionIndividual:
        return TrapDistribution(
            distribution_nodes = self._distribution_nodes,
            trap_amount = self._trap_amount,
            random_initialization = True,
        )

    def mutate(self, distribution: TrapDistribution) -> TrapDistribution:
        if random.random() > .3:
            for i in range(random.randint(1, 5)):
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
        else:
            for i in range(random.randint(1, 2)):
                first_group = random.choice(
                    [
                        group
                        for group in
                        distribution.traps
                        if group
                    ]
                )
                possible_second_groups = [
                    group
                    for group in
                    distribution.traps
                    if group != first_group and group
                ]
                if not possible_second_groups:
                    continue
                second_group = random.choice(
                    possible_second_groups
                )

                first = first_group.pop(
                    random.randint(
                        0,
                        len(first_group) - 1,
                    )
                )
                second = second_group.pop(
                    random.randint(
                        0,
                        len(second_group) - 1,
                    )
                )

                first_group.append(second)
                second_group.append(first)

        return distribution

    def mate(
        self,
        first: TrapDistribution,
        second: TrapDistribution,
    ) -> t.Tuple[TrapDistribution, TrapDistribution]:
        locations = {
            node: []
            for node in
            self.distribution_nodes
        }

        for distribution in (first, second):
            for i, traps in enumerate(distribution.traps):
                for node in traps:
                    locations[node].append(i)

        for distribution in (first, second):
            traps = [
                []
                for _ in
                range(self.trap_amount)
            ]

            for node, possibilities in locations.items():
                traps[random.choice(possibilities)].append(node)

            distribution.traps = traps

        return first, second
