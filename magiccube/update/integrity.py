from __future__ import annotations

import typing as t

from abc import ABC, abstractmethod
from collections import defaultdict

from magiccube.collections.nodecollection import ConstrainedNode
from yeetlong.multiset import FrozenMultiset

from magiccube.update.cubeupdate import CubeUpdater


class IntegrityWarning(ABC):

    @abstractmethod
    def check(self, updater: CubeUpdater) -> t.Optional[IntegrityWarning]:
        pass


class ChangedSize(IntegrityWarning):

    def __init__(self, size_delta: int):
        self._size_delta = size_delta

    def check(self, updater: CubeUpdater) -> t.Optional[ChangedSize]:
        size_delta = sum(updater.patch.cube_delta_operation.cubeables.multiplicities())
        if size_delta == 0:
            return None

        return ChangedSize(size_delta)


class NodesWithoutGroups(IntegrityWarning):

    def __init__(self, nodes: FrozenMultiset[ConstrainedNode]):
        self._nodes = nodes

    def check(self, updater: CubeUpdater) -> t.Optional[NodesWithoutGroups]:
        nodes = FrozenMultiset(
            {
                node: multiplicity
                for node, multiplicity in
                updater.patch.node_delta_operation.nodes.items()
                if multiplicity > 0 and not node.groups
            }
        )

        if not nodes:
            return None

        return NodesWithoutGroups(nodes)


class PrintingMismatch(IntegrityWarning):

    def check(self, updater: CubeUpdater) -> t.Optional[PrintingMismatch]:
        cardboard_map = defaultdict(lambda : [])
        for printing in updater.cube.all_printings:
            cardboard_map[printing.cardboard].append(printing)
        


class IntegrityReport(object):

    def __init__(self, updater: CubeUpdater):
        self._updater = updater