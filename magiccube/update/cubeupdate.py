from __future__ import annotations

import typing as t

import copy

from yeetlong.multiset import Multiset

from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator
from mtgorp.models.persistent.printing import Printing

from magiccube.laps.traps.tree.printingtree import BorderedNode
from magiccube.laps.traps.trap import Trap,IntentionType
from magiccube.collections.cube import Cube
from magiccube.collections.nodecollection import NodeCollection, NodesDeltaOperation, ConstrainedNode
from magiccube.collections.delta import CubeDeltaOperation


class VerboseCubePatch(object):

    def __init__(self):
        self._removed_printings = []
        self._added_printings = []
        self._printings_moved_to_nodes = []
        self._added_nodes = []
        self._removed_nodes = []
        self._changed_nodes = []


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
        new_printings: Multiset[Printing] = Multiset(
            {
                printing: multiplicity
                for printing, multiplicity
                in self._cube_delta_operation.cubeables.items()
                if multiplicity > 0
            }
        )
        removed_printings: Multiset[Printing] = Multiset(
            {
                printing: -multiplicity
                for printing, multiplicity
                in self._cube_delta_operation.cubeables.items()
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

        printings_moved_to_nodes: Multiset[Printing] = Multiset()

        for printing in removed_printings:
            if printing in new_printings_alone_in_nodes:
                printings_moved_to_nodes.add(printing)
                new_nodes.remove(
                    new_printings_alone_in_nodes[printing].pop(),
                    1,
                )
                if not new_printings_alone_in_nodes[printing]:
                    del new_printings_alone_in_nodes[printing]

        removed_printings -= printings_moved_to_nodes

        removed_printings_alone_in_nodes: t.Dict[Printing, t.List[ConstrainedNode]] = {}

        for node in removed_nodes:
            if len(node.node.children) == 1:
                child = node.node.children.__iter__().__next__()
                try:
                    removed_printings_alone_in_nodes[child].append(node)
                except KeyError:
                    removed_printings_alone_in_nodes[child] = [node]

        nodes_moved_to_printings: Multiset[ConstrainedNode] = Multiset()

        for printing in new_printings:
            if printing in removed_printings_alone_in_nodes:
                nodes_moved_to_printings.add(
                    removed_printings_alone_in_nodes[printing].pop(),
                )
                if not removed_printings_alone_in_nodes[printing]:
                    del removed_printings_alone_in_nodes[printing]
                new_printings.remove(printing, 1)
                break

        removed_nodes -= nodes_moved_to_printings

        altered_nodes = []

        for new_node in new_nodes:
            for removed_node in copy.copy(removed_nodes):
                if new_node.node == removed_node.node:
                    removed_nodes.remove(removed_node, 1)
                    altered_nodes.append([removed_node, new_node])
                    break

        for _, new_node in altered_nodes:
            new_nodes.remove(new_node, 1)

        print('new printings'.ljust(30), new_printings)
        print('removed printings'.ljust(30), removed_printings)
        print('new nodes'.ljust(30), new_nodes)
        print('removed nodes'.ljust(30), removed_nodes)
        print('printings moved to nodes'.ljust(30), printings_moved_to_nodes)
        print('nodes moved to printings'.ljust(30), nodes_moved_to_printings)
        print('altered_nodes'.ljust(30), altered_nodes)

        return VerboseCubePatch()

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