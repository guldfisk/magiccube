from __future__ import annotations

import typing as t

from yeetlong.multiset import FrozenMultiset
from yeetlong.counters import FrozenCounter

from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator

from magiccube.laps.traps.tree.printingtree import PrintingNode


class ConstrainedNode(Serializeable):

    def __init__(self, value: float, node: PrintingNode, groups: t.Iterable[str] = ()):
        self._value = value
        self._node = node

        self._groups = frozenset(groups)
        if len(node.children) == 1:
            colors = node.children.__iter__().__next__().cardboard.front_card.color
            if len(colors) == 1:
                self._groups |= colors

    @property
    def value(self) -> float:
        return self._value

    @property
    def node(self) -> PrintingNode:
        return self._node

    @property
    def groups(self) -> t.FrozenSet[str]:
        return self._groups

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

    def __hash__(self) -> int:
        if not hasattr(self, '_hash'):
            setattr(self, '_hash', hash((self.node, self.value, self.groups)))
        return getattr(self, '_hash')

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._node == other._node
            and self._value == other._value
            and self._groups == other._groups
        )

    def __repr__(self):
        return f'CC({self.node})'

    def __deepcopy__(self, memodict: t.Dict):
        return self


class NodeCollection(Serializeable):

    def __init__(self, nodes: t.Iterable[ConstrainedNode]):
        self._nodes = nodes if isinstance(nodes, FrozenMultiset) else FrozenMultiset(nodes)

    @property
    def nodes(self) -> FrozenMultiset[ConstrainedNode]:
        return self._nodes

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


class NodesDeltaOperation(Serializeable):

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
            nodes={
                ConstrainedNode.deserialize(
                    node,
                    inflator,
                ): multiplicity
                for node, multiplicity in
                value['nodes']
            }
        )

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

        
        