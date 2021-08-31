from __future__ import annotations

import typing as t
from collections import defaultdict

from frozendict import frozendict

from yeetlong.counters import FrozenCounter
from yeetlong.multiset import FrozenMultiset

from mtgorp.models.interfaces import Printing
from mtgorp.models.serilization.serializeable import Serializeable, PersistentHashable, serialization_model, Inflator

from magiccube.laps.traps.tree.printingtree import PrintingNode


class GroupMap(Serializeable):

    def __init__(self, groups: t.Mapping[str, float]):
        self._groups = groups if isinstance(groups, frozendict) else frozendict(groups)

    @property
    def groups(self) -> t.Mapping[str, float]:
        return self._groups

    def normalized(self) -> GroupMap:
        max_weight = max(self._groups.values())
        return self.__class__(
            frozendict(
                (group, weight / max_weight)
                for group, weight in
                self._groups.items()
                if weight > 0
            )
        )

    def serialize(self) -> serialization_model:
        return {
            'groups': [
                (group, weight)
                for group, weight in
                self._groups.items()
            ]
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> GroupMap:
        return cls(
            frozendict(
                [
                    (group, weight)
                    for group, weight in
                    value['groups']
                ]
            )
        )

    def __iter__(self) -> t.Iterator[str]:
        return self._groups.__iter__()

    def __add__(self, other: t.Union[GroupMap, GroupMapDeltaOperation]) -> GroupMap:
        groups = defaultdict(lambda: 0, self._groups)
        for group, weight in other._groups.items():
            groups[group] += weight
            if not groups[group]:
                del groups[group]

        return self.__class__(groups)

    __radd__ = __add__

    def __sub__(self, other: t.Union[GroupMap, GroupMapDeltaOperation]) -> GroupMap:
        groups = defaultdict(lambda: 0, self._groups)
        for group, weight in other._groups.items():
            groups[group] -= weight
            if not groups[group]:
                del groups[group]

        return self.__class__(groups)

    __rsub__ = __sub__

    def __mul__(self, other: float):
        if other == 0:
            return self.__class__({})
        return self.__class__(
            (group, weight * other)
            for group, weight in
            self._groups.items()
        )

    __rmul__ = __mul__

    def __invert__(self):
        return self.__mul__(-1)

    def __hash__(self) -> int:
        return hash(self._groups)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._groups == other._groups
        )

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(
                group + ': ' + str(weight)
                for group, weight in
                self._groups.items()
            )
        )


class GroupMapDeltaOperation(Serializeable, PersistentHashable):

    def __init__(
        self,
        groups: t.Optional[t.Mapping[str, t.Optional[float]]] = None,
    ):
        self._groups = (
            frozendict()
            if groups is None else
            (
                groups
                if isinstance(groups, frozendict) else
                frozendict(groups)
            )
        )

    @property
    def groups(self) -> t.Mapping[str, t.Optional[float]]:
        return self._groups

    def serialize(self) -> serialization_model:
        return {
            'groups': [
                (group, weight)
                for group, weight in
                self._groups.items()
            ]
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> 'Serializeable':
        return cls(
            frozendict(
                [
                    (group, weight)
                    for group, weight in
                    value['groups']
                ]
            )
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        for group, weight in sorted(
            (
                (group, weight)
                for group, weight in
                self._groups.items()
            ),
            key = lambda pair: pair[0],
        ):
            yield group.encode('ASCII')
            yield str(weight).encode('ASCII')

    def __add__(self, other: GroupMapDeltaOperation) -> GroupMapDeltaOperation:
        groups = defaultdict(lambda: 0, self._groups)
        for group, weight in other._groups.items():
            groups[group] += weight
            if not groups[group]:
                del groups[group]

        return self.__class__(groups)

    __radd__ = __add__

    def __sub__(self, other: GroupMapDeltaOperation) -> GroupMapDeltaOperation:
        groups = defaultdict(lambda: 0, self._groups)
        for group, weight in other._groups.items():
            groups[group] -= weight
            if not groups[group]:
                del groups[group]

        return self.__class__(groups)

    __rsub__ = __sub__

    def __mul__(self, other: float):
        return self.__class__(
            {
                group: value * other
                for group, value in
                self._groups.items()
            }
        )

    __rmul__ = __mul__

    def __invert__(self):
        return self.__mul__(-1)

    def __hash__(self) -> int:
        return hash(self._groups)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._groups == other._groups
        )

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(
                group + ': ' + str(weight)
                for group, weight in
                self._groups.items()
            )
        )


class ConstrainedNode(Serializeable, PersistentHashable):

    def __init__(self, value: float, node: PrintingNode, groups: t.Iterable[str] = ()):
        self._value = value
        self._node = node

        self._groups = frozenset(group for group in (g.strip() for g in groups) if group)

    @property
    def value(self) -> float:
        return self._value

    @property
    def node(self) -> PrintingNode:
        return self._node

    @property
    def groups(self) -> t.FrozenSet[str]:
        return self._groups

    def get_minimal_string(self) -> str:
        return '({}, {} - {})'.format(
            self._node.get_minimal_string(identified_by_id = False),
            self.value,
            ', '.join(sorted(self._groups)),
        )

    def serialize(self) -> serialization_model:
        return {
            'node': self._node,
            'value': self._value,
            'groups': self._groups,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> 'ConstrainedNode':
        return cls(
            node = PrintingNode.deserialize(
                value['node'],
                inflator,
            ),
            value = value['value'],
            groups = value['groups'],
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.node.persistent_hash().encode('ASCII')
        yield str(self.value).encode('ASCII')
        for group in sorted(self.groups):
            yield group.encode('UTF-8')

    def __hash__(self) -> int:
        return hash((self._node, self._value, self._groups))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._node == other._node
            and self._value == other._value
            and self._groups == other._groups
        )

    def __repr__(self):
        return f'CC({self.node}, {self.groups}, {self.value})'

    def __deepcopy__(self, memodict: t.Dict):
        return self


class NodeCollection(Serializeable):

    def __init__(self, nodes: t.Iterable[ConstrainedNode]):
        self._nodes = nodes if isinstance(nodes, FrozenMultiset) else FrozenMultiset(nodes)
        self._nodes_map: t.Optional[t.Mapping[PrintingNode, ConstrainedNode]] = None

    @property
    def nodes(self) -> FrozenMultiset[ConstrainedNode]:
        return self._nodes

    def node_for_node(self, node: PrintingNode) -> t.Optional[ConstrainedNode]:
        if self._nodes_map is None:
            self._nodes_map = {
                constrained_node.node: constrained_node
                for constrained_node in
                self._nodes.distinct_elements()
            }

        return self._nodes_map.get(node)

    def serialize(self) -> serialization_model:
        return {
            'nodes': [
                node.serialize()
                for node in
                self._nodes
            ]
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> NodeCollection:
        return cls(
            nodes = (
                ConstrainedNode.deserialize(
                    node,
                    inflator
                )
                for node in
                value['nodes']
            )
        )

    def items(self) -> t.Iterable[t.Tuple[ConstrainedNode, int]]:
        return self._nodes.items()

    @property
    def all_printings(self) -> t.Iterator[Printing]:
        for node in self._nodes:
            yield from node.node

    def __iter__(self) -> t.Iterator[ConstrainedNode]:
        return self._nodes.__iter__()

    def __len__(self) -> int:
        return self._nodes.__len__()

    def __hash__(self) -> int:
        return hash(self._nodes)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._nodes == other._nodes
        )

    def __add__(self, other: t.Union[NodeCollection, NodesDeltaOperation]) -> NodeCollection:
        return self.__class__(
            self._nodes + other.nodes
        )

    def __sub__(self, other: t.Union[NodeCollection, NodesDeltaOperation]) -> NodeCollection:
        return self.__class__(
            self._nodes - other.nodes
        )

    def __repr__(self) -> str:
        return self._nodes.__repr__()


class NodesDeltaOperation(Serializeable, PersistentHashable):

    def __init__(
        self,
        nodes: t.Optional[t.Mapping[ConstrainedNode, int]] = None,
    ):
        self._nodes = (
            FrozenCounter()
            if nodes is None else
            FrozenCounter(nodes)
        )

    @property
    def nodes(self) -> FrozenCounter[ConstrainedNode]:
        return self._nodes

    @property
    def all_new_printings(self) -> t.Iterator[Printing]:
        for node, multiplicity in self._nodes.items():
            for _ in range(multiplicity):
                yield from node.node

    @property
    def all_removed_printings(self) -> t.Iterator[Printing]:
        for node, multiplicity in self._nodes.items():
            for _ in range(-multiplicity):
                yield from node.node

    def serialize(self) -> serialization_model:
        return {
            'nodes': (
                (node, multiplicity)
                for node, multiplicity
                in self._nodes.items()
            )
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> NodesDeltaOperation:
        return cls(
            nodes = {
                ConstrainedNode.deserialize(
                    node,
                    inflator,
                ): multiplicity
                for node, multiplicity in
                value['nodes']
            }
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        for persistent_hash, multiplicity in sorted(
            (
                (node.persistent_hash(), multiplicity)
                for node, multiplicity in
                self._nodes.items()
            ),
            key = lambda pair: pair[0],
        ):
            yield persistent_hash.encode('ASCII')
            yield str(multiplicity).encode('ASCII')

    def __hash__(self) -> int:
        return hash(self._nodes)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._nodes == other._nodes
        )

    def __add__(self, other: t.Union[NodesDeltaOperation, NodeCollection]) -> NodesDeltaOperation:
        return self.__class__(
            self._nodes + other.nodes
        )

    __radd__ = __add__

    def __sub__(self, other: t.Union[NodesDeltaOperation, NodeCollection]) -> NodesDeltaOperation:
        return self.__class__(
            self._nodes - other.nodes
        )

    __rsub__ = __sub__

    def __mul__(self, other: int) -> NodesDeltaOperation:
        return self.__class__(
            self._nodes * other
        )

    __rmul__ = __mul__

    def __invert__(self):
        return self.__class__(
            self._nodes * -1
        )

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            self._nodes,
        )
