from __future__ import annotations

import typing as t

from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator

from magiccube.laps.traps.tree.printingtree import BorderedNode
from magiccube.laps.traps.trap import Trap,IntentionType
from magiccube.collections.cube import Cube
from magiccube.collections.nodecollection import NodeCollection, NodesDeltaOperation
from magiccube.collections.delta import CubeDeltaOperation


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

    def serialize(self) -> serialization_model:
        return {
            'cube_delta': self._cube_delta_operation.serialize(),
            'nodes_delta': self._node_delta_operation.serialize(),
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CubePatch:
        return cls(
            cube_delta_operation = CubeDeltaOperation.deserialize(value['cube_delta'], inflator),
            node_delta_operation = NodesDeltaOperation.deserialize(value['nodes_delta'], inflator),
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