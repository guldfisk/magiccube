from __future__ import annotations

import typing as t
from abc import ABC, abstractmethod
import itertools

import copy

from yeetlong.multiset import Multiset

from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator
from mtgorp.models.persistent.printing import Printing

from magiccube.laps.traps.tree.printingtree import BorderedNode
from magiccube.laps.lap import Lap
from magiccube.laps.traps.trap import Trap,IntentionType
from magiccube.collections.cube import Cube, Cubeable
from magiccube.collections.nodecollection import NodeCollection, NodesDeltaOperation, ConstrainedNode
from magiccube.collections.delta import CubeDeltaOperation


class CubeChange(ABC):

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass


class NewCubeable(CubeChange):

    def __init__(self, cubeable: Cubeable):
        self._cubeable = cubeable

    @property
    def cubeable(self) -> Cubeable:
        return self._cubeable

    def __hash__(self) -> int:
        return hash(self._cubeable)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._cubeable == other._cubeable
        )

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            self._cubeable,
        )


class RemovedCubeable(CubeChange):

    def __init__(self, cubeable: Cubeable):
        self._cubeable = cubeable

    @property
    def cubeable(self) -> Cubeable:
        return self._cubeable

    def __hash__(self) -> int:
        return hash(self._cubeable)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._cubeable == other._cubeable
        )

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            self._cubeable,
        )


class NewNode(CubeChange):

    def __init__(self, node: ConstrainedNode):
        self._node = node

    @property
    def node(self) -> ConstrainedNode:
        return self._node

    def __hash__(self) -> int:
        return hash(self._node)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._node == other._node
        )

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            self._node,
        )


class RemovedNode(CubeChange):

    def __init__(self, node: ConstrainedNode):
        self._node = node

    @property
    def node(self) -> ConstrainedNode:
        return self._node

    def __hash__(self) -> int:
        return hash(self._node)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._node == other._node
        )

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            self._node,
        )


class PrintingToNode(CubeChange):

    def __init__(self, before: Printing, after: ConstrainedNode):
        self._before = before
        self._after = after

    @property
    def before(self) -> Printing:
        return self._before

    @property
    def after(self) -> ConstrainedNode:
        return self._after

    def __hash__(self) -> int:
        return hash(
            (
                self._before,
                self._after,
            )
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and other ._before == self._before
            and other._after == self._after
        )

    def __repr__(self) -> str:
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self._before,
            self._after,
        )


class NodeToPrinting(CubeChange):

    def __init__(self, before: ConstrainedNode, after: Printing):
        self._before = before
        self._after = after

    @property
    def before(self) -> ConstrainedNode:
        return self._before

    @property
    def after(self) -> Printing:
        return self._after

    def __hash__(self) -> int:
        return hash(
            (
                self._before,
                self._after,
            )
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and other ._before == self._before
            and other._after == self._after
        )

    def __repr__(self) -> str:
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self._before,
            self._after,
        )


class AlteredNode(CubeChange):

    def __init__(self, before: ConstrainedNode, after: ConstrainedNode):
        self._before = before
        self._after = after

    @property
    def before(self) -> ConstrainedNode:
        return self._before

    @property
    def after(self) -> ConstrainedNode:
        return self._after

    def __hash__(self) -> int:
        return hash(
            (
                self._before,
                self._after,
            )
        )

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and other ._before == self._before
            and other._after == self._after
        )

    def __repr__(self) -> str:
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self._before,
            self._after,
        )


class VerboseCubePatch(object):

    def __init__(self, changes: t.Iterable[CubeChange]):
        self._changes = Multiset(changes)

    @property
    def changes(self) -> Multiset[CubeChange]:
        return self._changes

    def __hash__(self) -> int:
        return hash(self._changes)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._changes == other._changes
        )

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            {
                change: multiplicity
                for change, multiplicity in
                self._changes.items()
            },
        )


class CubePatch(Serializeable):

    def __init__(
        self,
        cube_delta_operation: t.Optional[CubeDeltaOperation] = None,
        node_delta_operation: t.Optional[NodesDeltaOperation] = None,
    ):
        self._cube_delta_operation = CubeDeltaOperation() if cube_delta_operation is None else cube_delta_operation
        self._node_delta_operation = NodesDeltaOperation() if node_delta_operation is None else node_delta_operation

    @property
    def cube_delta_operation(self) -> CubeDeltaOperation:
        return self._cube_delta_operation

    @property
    def node_delta_operation(self) -> NodesDeltaOperation:
        return self._node_delta_operation

    @property
    def as_verbose(self) -> VerboseCubePatch:
        new_laps: Multiset[Lap] = Multiset(
            {
                lap: multiplicity
                for lap, multiplicity
                in self._cube_delta_operation.laps
                if multiplicity > 0
            }
        )
        removed_laps: Multiset[Lap] = Multiset(
            {
                lap: -multiplicity
                for lap, multiplicity
                in self._cube_delta_operation.laps
                if multiplicity < 0
            }
        )

        new_printings: Multiset[Printing] = Multiset(
            {
                printing: multiplicity
                for printing, multiplicity
                in self._cube_delta_operation.printings
                if multiplicity > 0
            }
        )
        removed_printings: Multiset[Printing] = Multiset(
            {
                printing: -multiplicity
                for printing, multiplicity
                in self._cube_delta_operation.printings
                if multiplicity < 0
            }
        )

        new_nodes: Multiset[ConstrainedNode] = Multiset(
            {
                node: multiplicity
                for node, multiplicity
                in self._node_delta_operation.nodes.items()
                if multiplicity > 0
            }
        )

        removed_nodes: Multiset[ConstrainedNode] = Multiset(
            {
                node: -multiplicity
                for node, multiplicity
                in self._node_delta_operation.nodes.items()
                if multiplicity < 0
            }
        )

        new_printings_alone_in_nodes: t.Dict[Printing, t.List[ConstrainedNode]] = {}

        for node in new_nodes:
            if len(node.node.children) == 1:
                child = node.node.children.__iter__().__next__()
                try:
                    new_printings_alone_in_nodes[child].append(node)
                except KeyError:
                    new_printings_alone_in_nodes[child] = [node]

        printings_moved_to_nodes: Multiset[t.Tuple[Printing, ConstrainedNode]] = Multiset()

        for printing in removed_printings:
            if printing in new_printings_alone_in_nodes:
                node = new_printings_alone_in_nodes[printing].pop()
                printings_moved_to_nodes.add((printing, node))
                new_nodes.remove(
                    node,
                    1,
                )
                if not new_printings_alone_in_nodes[printing]:
                    del new_printings_alone_in_nodes[printing]

        removed_printings -= Multiset(printing for printing, _ in printings_moved_to_nodes.items())

        removed_printings_alone_in_nodes: t.Dict[Printing, t.List[ConstrainedNode]] = {}

        for node in removed_nodes:
            if len(node.node.children) == 1:
                child = node.node.children.__iter__().__next__()
                try:
                    removed_printings_alone_in_nodes[child].append(node)
                except KeyError:
                    removed_printings_alone_in_nodes[child] = [node]

        nodes_moved_to_printings: Multiset[t.Tuple[ConstrainedNode, Printing]] = Multiset()

        for printing in new_printings:
            if printing in removed_printings_alone_in_nodes:
                node = removed_printings_alone_in_nodes[printing].pop()
                nodes_moved_to_printings.add((node, printing))
                if not removed_printings_alone_in_nodes[printing]:
                    del removed_printings_alone_in_nodes[printing]
                new_printings.remove(printing, 1)
                break

        removed_nodes -= Multiset(node for node, _ in nodes_moved_to_printings.items())

        altered_nodes = []

        for new_node in new_nodes:
            for removed_node in copy.copy(removed_nodes):
                if new_node.node == removed_node.node:
                    removed_nodes.remove(removed_node, 1)
                    altered_nodes.append([removed_node, new_node])
                    break

        for _, new_node in altered_nodes:
            new_nodes.remove(new_node, 1)

        return VerboseCubePatch(
            itertools.chain(
                (
                    NewCubeable(lap)
                    for lap in
                    new_laps
                ),
                (
                    RemovedCubeable(lap)
                    for lap in
                    removed_laps
                ),
                (
                    NewCubeable(printing)
                    for printing in
                    new_printings
                ),
                (
                    RemovedCubeable(printing)
                    for printing in
                    removed_printings
                ),
                (
                    NewNode(node)
                    for node in
                    new_nodes
                ),
                (
                    RemovedNode(node)
                    for node in
                    removed_nodes
                ),
                (
                    PrintingToNode(printing, node)
                    for printing, node in
                    printings_moved_to_nodes
                ),
                (
                    NodeToPrinting(node, printing)
                    for node, printing in
                    nodes_moved_to_printings
                ),
                (
                    AlteredNode(before, after)
                    for before, after in
                    altered_nodes
                )
            )
        )

    def serialize(self) -> serialization_model:
        return {
            'cube_delta': self._cube_delta_operation.serialize(),
            'nodes_delta': self._node_delta_operation.serialize(),
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CubePatch:
        return cls(
            cube_delta_operation = CubeDeltaOperation.deserialize(value['cube_delta'], inflator),
            node_delta_operation = (
                NodesDeltaOperation.deserialize(value['nodes_delta'], inflator)
                if 'nodes_delta' in value else
                NodesDeltaOperation()
            ),
        )

    def __hash__(self) -> int:
        return hash(
            (
                self._cube_delta_operation,
                self._node_delta_operation,
            )
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._cube_delta_operation == other._cube_delta_operation
            and self._node_delta_operation == other._node_delta_operation
        )
    
    def __repr__(self):
        return '{}({}, {})'.format(
            self.__class__.__name__,
            self._cube_delta_operation,
            self._node_delta_operation,
        )

    def __add__(self, other: CubePatch) -> CubePatch:
        return self.__class__(
            self._cube_delta_operation + other._cube_delta_operation,
            self._node_delta_operation + other._node_delta_operation,
        )

    def __sub__(self, other: CubePatch) -> CubePatch:
        return self.__class__(
            self._cube_delta_operation - other._cube_delta_operation,
            self._node_delta_operation - other._node_delta_operation,
        )


class CubeUpdater(object):
    
    def __init__(
        self,
        cube: Cube,
        node_collection: NodeCollection,
        patch: CubePatch,
    ):
        self._cube = cube
        self._node_collection = node_collection
        self._patch = patch

        self._new_no_garbage_cube = None
        self._new_nodes = None

    @property
    def new_no_garbage_cube(self):
        if self._new_no_garbage_cube is None:
            self._new_no_garbage_cube = (
                self._cube
                + ~CubeDeltaOperation(
                    self._cube.garbage_traps.elements()
                )
                + self._patch.cube_delta_operation
            )
        
        return self._new_no_garbage_cube

    @property
    def new_nodes(self):
        if self._new_nodes is None:
            self._new_nodes = self._node_collection + self._patch.node_delta_operation

        return self._new_nodes

    @property
    def new_garbage_trap_amount(self):
        return len(self._cube) - len(self.new_no_garbage_cube)

    def generate_garbage_traps(
        self,
        nodes: NodeCollection,
        amount: int,
        delta: int,
    ) -> t.Iterable[BorderedNode]:
        raise NotImplemented

    def old_average_trap_size(self) -> float:
        return len(self._node_collection) / len(self._cube.garbage_traps)

    def new_average_trap_size(self) -> float:
        return len(self.new_nodes) / self.new_garbage_trap_amount

    def update(self, delta: int = 0):
        return self.new_no_garbage_cube + (
            Trap(
                node = node,
                intention_type = IntentionType.GARBAGE,
            )
            for node in
            self.generate_garbage_traps(
                nodes=self.new_nodes,
                amount=self.new_garbage_trap_amount,
                delta=delta,
            )
        )