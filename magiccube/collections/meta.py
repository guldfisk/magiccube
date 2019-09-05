from __future__ import annotations

import typing as t

from magiccube.collections.cube import Cube
from magiccube.collections.nodecollection import NodeCollection, GroupMap
from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator


class MetaCube(Serializeable):

    def __init__(self, cube: Cube, nodes: NodeCollection, groups: GroupMap):
        self._cube = cube
        self._nodes = nodes
        self._groups = groups

    @property
    def cube(self) -> Cube:
        return self._cube

    @property
    def node_collection(self) -> NodeCollection:
        return self._nodes

    @property
    def group_map(self) -> GroupMap:
        return self._groups

    def serialize(self) -> serialization_model:
        return {
            'cube': self._cube,
            'nodes': self._nodes,
            'groups': self._groups,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> MetaCube:
        return cls(
            Cube.deserialize(value['cube'], inflator),
            NodeCollection.deserialize(value['nodes'], inflator),
            GroupMap.deserialize(value['groups'], inflator),
        )

    def __hash__(self) -> int:
        return hash((self._cube, self._nodes, self._groups))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._cube == other._cube
            and self._nodes == other._nodes
            and self._groups == other._groups
        )
