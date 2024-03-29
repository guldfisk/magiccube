from __future__ import annotations

import copy
import itertools
import typing as t
from abc import abstractmethod
from collections import defaultdict
from enum import Enum

from mtgorp.models.collections.cardboardset import CardboardSet
from mtgorp.models.interfaces import Cardboard, Printing
from mtgorp.models.serilization.serializeable import (
    Inflator,
    PersistentHashable,
    Serializeable,
    serialization_model,
)
from orp.models import OrpBase
from yeetlong.multiset import FrozenMultiset, Multiset

from magiccube.collections.cube import Cube, Cubeable
from magiccube.collections.delta import CubeDeltaOperation
from magiccube.collections.infinites import InfinitesDeltaOperation
from magiccube.collections.laps import TrapCollection
from magiccube.collections.meta import MetaCube
from magiccube.collections.nodecollection import (
    ConstrainedNode,
    GroupMap,
    GroupMapDeltaOperation,
    NodeCollection,
    NodesDeltaOperation,
)
from magiccube.laps.lap import Lap
from magiccube.laps.purples.purple import Purple
from magiccube.laps.tickets.ticket import Ticket
from magiccube.laps.traps.trap import Trap
from magiccube.laps.traps.tree.printingtree import PrintingNode


class CubeChange(Serializeable, PersistentHashable):
    class Category(Enum):
        ADDITION = "addition"
        SUBTRACTION = "subtraction"
        MODIFICATION = "modification"
        TRANSFER = "transfer"

    category = Category.MODIFICATION

    @abstractmethod
    def explain(self) -> str:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def as_patch(self) -> CubePatch:
        pass


class AddInfinite(CubeChange):
    category = CubeChange.Category.ADDITION

    def __init__(self, cardboard: Cardboard):
        self._cardboard = cardboard

    def explain(self) -> str:
        return f"add new infinite: {self._cardboard.name}"

    def __hash__(self) -> int:
        return hash(self._cardboard.name)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self._cardboard == other._cardboard

    def as_patch(self) -> CubePatch:
        return CubePatch(
            infinites_delta_operation=InfinitesDeltaOperation(added=CardboardSet((self._cardboard,))),
        )

    def serialize(self) -> serialization_model:
        return {
            "cardboard": self._cardboard,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> AddInfinite:
        return cls(inflator.inflate(Cardboard, value["cardboard"]))

    def _calc_persistent_hash(self) -> t.Iterator[t.ByteString]:
        yield self._cardboard.name.encode("UTF-8")


class RemoveInfinite(CubeChange):
    category = CubeChange.Category.SUBTRACTION

    def __init__(self, cardboard: Cardboard):
        self._cardboard = cardboard

    def explain(self) -> str:
        return f"remove infinite: {self._cardboard.name}"

    def __hash__(self) -> int:
        return hash(self._cardboard.name)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self._cardboard == other._cardboard

    def as_patch(self) -> CubePatch:
        return CubePatch(
            infinites_delta_operation=InfinitesDeltaOperation(removed=CardboardSet((self._cardboard,))),
        )

    def serialize(self) -> serialization_model:
        return {
            "cardboard": self._cardboard,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> RemoveInfinite:
        return cls(inflator.inflate(Cardboard, value["cardboard"]))

    def _calc_persistent_hash(self) -> t.Iterator[t.ByteString]:
        yield self._cardboard.name.encode("UTF-8")


class AddGroup(CubeChange):
    category = CubeChange.Category.ADDITION

    def __init__(self, group: str, value: float):
        self._group = group
        self._value = value

    def explain(self) -> str:
        return f"{self._group}: {round(self._value, 2)}"

    def __hash__(self) -> int:
        return hash(self._group)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self._group == other._group

    def as_patch(self) -> CubePatch:
        return CubePatch(
            group_map_delta_operation=GroupMapDeltaOperation(
                {
                    self._group: self._value,
                }
            )
        )

    def serialize(self) -> serialization_model:
        return {
            "group": self._group,
            "value": self._value,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> AddGroup:
        return cls(
            value["group"],
            value["value"],
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("ASCII")
        yield self._group.encode("UTF-8")


class GroupWeightChange(CubeChange):
    category = CubeChange.Category.MODIFICATION

    def __init__(self, group: str, old_value: float, new_value: float):
        self._group = group
        self._old_value = old_value
        self._new_value = new_value

    def explain(self) -> str:
        return f"{self._group}: {round(self._old_value, 2)} -> {round(self._new_value, 2)}"

    def __hash__(self) -> int:
        return hash(self._group)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self._group == other._group

    def as_patch(self) -> CubePatch:
        return CubePatch(
            group_map_delta_operation=GroupMapDeltaOperation(
                {
                    self._group: self._new_value - self._old_value,
                }
            )
        )

    def serialize(self) -> serialization_model:
        return {
            "group": self._group,
            "old_value": self._old_value,
            "new_value": self._new_value,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> GroupWeightChange:
        return cls(
            group=value["group"],
            old_value=value["old_value"],
            new_value=value["new_value"],
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("ASCII")
        yield self._group.encode("UTF-8")


class RemoveGroup(CubeChange):
    category = CubeChange.Category.SUBTRACTION

    def __init__(self, group: str, weight: float):
        self._group = group
        self._weight = weight

    def explain(self) -> str:
        return self._group

    def __hash__(self) -> int:
        return hash(self._group)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self._group == other._group

    def as_patch(self) -> CubePatch:
        return CubePatch(
            group_map_delta_operation=GroupMapDeltaOperation(
                {
                    self._group: self._weight,
                }
            )
        )

    def serialize(self) -> serialization_model:
        return {
            "group": self._group,
            "weight": self._weight,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> RemoveGroup:
        return cls(
            value["group"],
            value["weight"],
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("ASCII")
        yield self._group.encode("UTF-8")


class CubeableCubeChange(CubeChange):
    def __init__(self, cubeable: Cubeable):
        super().__init__()
        self._cubeable = cubeable

    @property
    def cubeable(self) -> Cubeable:
        return self._cubeable

    def serialize(self) -> serialization_model:
        return {
            "cubeable": self._cubeable,
            "type": self._cubeable.__class__.__name__,
        }

    _cubeables_name_map = {klass.__name__: klass for klass in (Trap, Ticket, Purple)}

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> "Serializeable":
        return cls(
            inflator.inflate(Printing, value["cubeable"])
            if value["type"] == "Printing"
            else cls._cubeables_name_map[value["type"]].deserialize(
                value["cubeable"],
                inflator,
            )
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("ASCII")
        if isinstance(self._cubeable, OrpBase):
            yield str(self._cubeable.primary_key).encode("ASCII")
        else:
            yield self._cubeable.persistent_hash().encode("ASCII")

    def __hash__(self) -> int:
        return hash(self._cubeable)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self._cubeable == other._cubeable

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            self._cubeable,
        )

    def explain(self) -> str:
        if isinstance(self._cubeable, Printing):
            return self._cubeable.full_name()
        if isinstance(self._cubeable, Trap):
            return self._cubeable.node.get_minimal_string(identified_by_id=False)
        if isinstance(self._cubeable, Ticket):
            return "Ticket"
        return "Purple"

    @abstractmethod
    def as_patch(self) -> CubePatch:
        pass


class NewCubeable(CubeableCubeChange):
    category = CubeChange.Category.ADDITION

    def as_patch(self) -> CubePatch:
        return CubePatch(
            CubeDeltaOperation(
                {
                    self._cubeable: 1,
                }
            )
        )


class RemovedCubeable(CubeableCubeChange):
    category = CubeChange.Category.SUBTRACTION

    def as_patch(self) -> CubePatch:
        return CubePatch(
            CubeDeltaOperation(
                {
                    self._cubeable: -1,
                }
            )
        )


class NodeCubeChange(CubeChange):
    def __init__(self, node: ConstrainedNode):
        super().__init__()
        self._node = node

    @property
    def node(self) -> ConstrainedNode:
        return self._node

    def explain(self) -> str:
        return self._node.get_minimal_string()

    def serialize(self) -> serialization_model:
        return {
            "node": self._node,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> NodeCubeChange:
        return cls(ConstrainedNode.deserialize(value["node"], inflator))

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("ASCII")
        yield self._node.persistent_hash().encode("ASCII")

    def __hash__(self) -> int:
        return hash(self._node)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self._node == other._node

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            self._node,
        )

    @abstractmethod
    def as_patch(self) -> CubePatch:
        pass


class NewNode(NodeCubeChange):
    category = CubeChange.Category.ADDITION

    def as_patch(self) -> CubePatch:
        return CubePatch(
            node_delta_operation=NodesDeltaOperation(
                {
                    self._node: 1,
                }
            )
        )


class RemovedNode(NodeCubeChange):
    category = CubeChange.Category.SUBTRACTION

    def as_patch(self) -> CubePatch:
        return CubePatch(
            node_delta_operation=NodesDeltaOperation(
                {
                    self._node: -1,
                }
            )
        )


class PrintingsToNode(CubeChange):
    category = CubeChange.Category.TRANSFER

    def __init__(self, before: t.Iterable[Printing], after: ConstrainedNode):
        self._before = before if isinstance(before, FrozenMultiset) else FrozenMultiset(before)
        self._after = after

    @property
    def before(self) -> FrozenMultiset[Printing]:
        return self._before

    @property
    def after(self) -> ConstrainedNode:
        return self._after

    def explain(self) -> str:
        return "{} -> {}".format(
            ", ".join(
                (
                    ((str(multiplicity) + "x ") if multiplicity != 1 else "") + printing.full_name()
                    for printing, multiplicity in self._before.items()
                )
            ),
            self._after.get_minimal_string(),
        )

    def serialize(self) -> serialization_model:
        return {
            "before": self._before,
            "after": self._after,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> "Serializeable":
        return cls(
            inflator.inflate_all(Printing, value["before"]),
            ConstrainedNode.deserialize(value["after"], inflator),
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("ASCII")
        for _id in sorted((printing.id for printing in self._before)):
            yield str(_id).encode("ASCII")
        yield self._after.persistent_hash().encode("ASCII")

    def __hash__(self) -> int:
        return hash(
            (
                self._before,
                self._after,
            )
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and other._before == self._before and other._after == self._after

    def __repr__(self) -> str:
        return "{}({}, {})".format(
            self.__class__.__name__,
            self._before,
            self._after,
        )

    def as_patch(self) -> CubePatch:
        return CubePatch(
            CubeDeltaOperation({printing: -multiplicity for printing, multiplicity in self._before.items()}),
            NodesDeltaOperation(
                {
                    self._after: 1,
                }
            ),
        )


class TrapNodeTransfer(CubeChange):
    category = CubeChange.Category.TRANSFER

    def __init__(self, trap: Trap, node: ConstrainedNode):
        self._trap = trap
        self._node = node

    @abstractmethod
    def explain(self) -> str:
        pass

    def __hash__(self) -> int:
        return hash((self._trap, self._node))

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and other._trap == self._trap and other._node == self._node

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            self._node,
        )

    @abstractmethod
    def as_patch(self) -> CubePatch:
        pass

    def serialize(self) -> serialization_model:
        return {
            "trap": self._trap,
            "node": self._node,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> "Serializeable":
        return cls(
            trap=Trap.deserialize(value["trap"], inflator),
            node=ConstrainedNode.deserialize(value["node"], inflator),
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("ASCII")
        yield self._trap.persistent_hash().encode("ASCII")
        yield self._node.persistent_hash().encode("ASCII")


class TrapToNode(TrapNodeTransfer):
    def explain(self) -> str:
        return "trap -> {}".format(self._node.get_minimal_string())

    def as_patch(self) -> CubePatch:
        return CubePatch(
            CubeDeltaOperation(
                {
                    self._trap: -1,
                }
            ),
            NodesDeltaOperation(
                {
                    self._node: 1,
                }
            ),
        )


class NodeToTrap(TrapNodeTransfer):
    def explain(self) -> str:
        return "{} -> Trap".format(self._node.get_minimal_string())

    def as_patch(self) -> CubePatch:
        return CubePatch(
            CubeDeltaOperation(
                {
                    self._trap: 1,
                }
            ),
            NodesDeltaOperation(
                {
                    self._node: -1,
                }
            ),
        )


class NodeToPrintings(CubeChange):
    category = CubeChange.Category.TRANSFER

    def __init__(self, before: ConstrainedNode, after: t.Iterable[Printing]):
        self._before = before
        self._after = after if isinstance(after, FrozenMultiset) else FrozenMultiset(after)

    @property
    def before(self) -> ConstrainedNode:
        return self._before

    @property
    def after(self) -> FrozenMultiset[Printing]:
        return self._after

    def explain(self) -> str:
        return "{} -> {}".format(
            self._before.get_minimal_string(),
            ", ".join(
                (
                    ((str(multiplicity) + "x ") if multiplicity != 1 else "") + printing.full_name()
                    for printing, multiplicity in self._after.items()
                )
            ),
        )

    def serialize(self) -> serialization_model:
        return {
            "before": self._before,
            "after": self._after,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> "Serializeable":
        return cls(
            ConstrainedNode.deserialize(value["before"], inflator),
            inflator.inflate_all(Printing, value["after"]),
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("ASCII")
        for _id in sorted((printing.id for printing in self._after)):
            yield str(_id).encode("ASCII")
        yield self._before.persistent_hash().encode("ASCII")

    def __hash__(self) -> int:
        return hash(
            (
                self._before,
                self._after,
            )
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and other._before == self._before and other._after == self._after

    def __repr__(self) -> str:
        return "{}({}, {})".format(
            self.__class__.__name__,
            self._before,
            self._after,
        )

    def as_patch(self) -> CubePatch:
        return CubePatch(
            CubeDeltaOperation({printing: multiplicity for printing, multiplicity in self._after.items()}),
            NodesDeltaOperation(
                {
                    self._before: -1,
                }
            ),
        )


class AlteredNode(CubeChange):
    category = CubeChange.Category.MODIFICATION

    def __init__(self, before: ConstrainedNode, after: ConstrainedNode):
        self._before = before
        self._after = after

    @property
    def before(self) -> ConstrainedNode:
        return self._before

    @property
    def after(self) -> ConstrainedNode:
        return self._after

    def explain(self) -> str:
        added_groups = self._after.groups - self._before.groups
        removed_groups = self._before.groups - self._after.groups
        s = self._after.node.get_minimal_string(identified_by_id=False)
        for group in added_groups:
            s += " +" + group
        for group in removed_groups:
            s += " -" + group
        if self._before.value != self._after.value:
            s += f" {self._before.value} -> {self.after.value}"

        return s

    def serialize(self) -> serialization_model:
        return {
            "before": self._before,
            "after": self._after,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> "Serializeable":
        return cls(
            ConstrainedNode.deserialize(value["before"], inflator),
            ConstrainedNode.deserialize(value["after"], inflator),
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("ASCII")
        yield self._before.persistent_hash().encode("ASCII")
        yield self._after.persistent_hash().encode("ASCII")

    def __hash__(self) -> int:
        return hash(
            (
                self._before,
                self._after,
            )
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and other._before == self._before and other._after == self._after

    def __repr__(self) -> str:
        return "{}({}, {})".format(
            self.__class__.__name__,
            self._before,
            self._after,
        )

    def as_patch(self) -> CubePatch:
        return CubePatch(
            node_delta_operation=NodesDeltaOperation(
                {
                    self._before: -1,
                    self._after: 1,
                }
            ),
        )


class PrintingChange(CubeChange):
    category = CubeChange.Category.MODIFICATION

    def __init__(self, before: Printing, after: Printing):
        self._before = before
        self._after = after

    def explain(self) -> str:
        return f"{self._after.cardboard.name} {self._before.expansion.code} -> {self._after.expansion.code}"

    def __hash__(self) -> int:
        return hash((self._before, self._after))

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self._before == other._before and self._after == other._after

    def as_patch(self) -> CubePatch:
        return CubePatch(
            CubeDeltaOperation(
                {
                    self._before: -1,
                    self._after: 1,
                }
            ),
        )

    def serialize(self) -> serialization_model:
        return {
            "before": self._before,
            "after": self._after,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> PrintingChange:
        return cls(
            inflator.inflate(Printing, value["before"]),
            inflator.inflate(Printing, value["after"]),
        )

    def _calc_persistent_hash(self) -> t.Iterable[t.ByteString]:
        yield self.__class__.__name__.encode("ASCII")
        yield str(self._before.id).encode("ASCII")
        yield str(self._after.id).encode("ASCII")

    def __repr__(self) -> str:
        return "{}({}, {})".format(
            self.__class__.__name__,
            self._before,
            self._after,
        )


CUBE_CHANGE_MAP: t.Dict[str, t.Type[CubeChange]] = {
    klass.__name__: klass
    for klass in (
        AddInfinite,
        RemoveInfinite,
        AddGroup,
        RemoveGroup,
        GroupWeightChange,
        NewCubeable,
        RemovedCubeable,
        NewNode,
        RemovedNode,
        PrintingsToNode,
        NodeToPrintings,
        TrapToNode,
        NodeToTrap,
        AlteredNode,
    )
}


class VerboseCubePatch(Serializeable):
    def __init__(self, changes: t.Iterable[CubeChange]):
        self._changes = Multiset(changes)

    @property
    def changes(self) -> Multiset[CubeChange]:
        return self._changes

    def serialize(self) -> serialization_model:
        return {
            "changes": [
                (
                    change.serialize(),
                    multiplicity,
                    change.__class__.__name__,
                )
                for change, multiplicity in self._changes.items()
            ]
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> VerboseCubePatch:
        return cls(
            {
                CUBE_CHANGE_MAP[klass].deserialize(change, inflator): multiplicity
                for change, multiplicity, klass in value["changes"]
            }
        )

    def __hash__(self) -> int:
        return hash(self._changes)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and self._changes == other._changes

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            {change: multiplicity for change, multiplicity in self._changes.items()},
        )


class CubePatch(Serializeable, PersistentHashable):
    def __init__(
        self,
        cube_delta_operation: t.Optional[CubeDeltaOperation] = None,
        node_delta_operation: t.Optional[NodesDeltaOperation] = None,
        group_map_delta_operation: t.Optional[GroupMapDeltaOperation] = None,
        infinites_delta_operation: t.Optional[InfinitesDeltaOperation] = None,
    ):
        self._cube_delta_operation = CubeDeltaOperation() if cube_delta_operation is None else cube_delta_operation
        self._node_delta_operation = NodesDeltaOperation() if node_delta_operation is None else node_delta_operation
        self._group_map_delta_operation = (
            GroupMapDeltaOperation() if group_map_delta_operation is None else group_map_delta_operation
        )
        self._infinites_delta_operation = (
            InfinitesDeltaOperation() if infinites_delta_operation is None else infinites_delta_operation
        )

    @property
    def cube_delta_operation(self) -> CubeDeltaOperation:
        return self._cube_delta_operation

    @property
    def node_delta_operation(self) -> NodesDeltaOperation:
        return self._node_delta_operation

    @property
    def group_map_delta_operation(self) -> GroupMapDeltaOperation:
        return self._group_map_delta_operation

    @property
    def infinites_delta_operation(self) -> InfinitesDeltaOperation:
        return self._infinites_delta_operation

    @classmethod
    def from_meta_delta(cls, from_meta: MetaCube, to_meta: MetaCube) -> CubePatch:
        return cls(
            cube_delta_operation=(
                CubeDeltaOperation(to_meta.cube.cubeables.elements())
                - CubeDeltaOperation(from_meta.cube.cubeables.elements())
            ),
            node_delta_operation=(
                NodesDeltaOperation(to_meta.node_collection.nodes.elements())
                - NodesDeltaOperation(from_meta.node_collection.nodes.elements())
            ),
            group_map_delta_operation=(
                GroupMapDeltaOperation(to_meta.group_map.groups) - GroupMapDeltaOperation(from_meta.group_map.groups)
            ),
            infinites_delta_operation=InfinitesDeltaOperation.from_change(
                from_meta.infinites,
                to_meta.infinites,
            ),
        )

    def as_verbose(self, meta_cube: MetaCube) -> VerboseCubePatch:
        group_updates = set()

        for group, new_weight in self.group_map_delta_operation.groups.items():
            current_weight = meta_cube.group_map.groups.get(group)
            if current_weight is None:
                group_updates.add(AddGroup(group, new_weight))
            else:
                if -new_weight == current_weight:
                    group_updates.add(
                        RemoveGroup(
                            group,
                            new_weight,
                        )
                    )
                else:
                    group_updates.add(
                        GroupWeightChange(
                            group,
                            current_weight,
                            current_weight + new_weight,
                        )
                    )

        new_laps: Multiset[Lap] = Multiset(
            {lap: multiplicity for lap, multiplicity in self._cube_delta_operation.laps if multiplicity > 0}
        )
        removed_laps: Multiset[Lap] = Multiset(
            {lap: -multiplicity for lap, multiplicity in self._cube_delta_operation.laps if multiplicity < 0}
        )

        new_printings: Multiset[Printing] = Multiset(
            {
                printing: multiplicity
                for printing, multiplicity in self._cube_delta_operation.printings
                if multiplicity > 0
            }
        )
        removed_printings: Multiset[Printing] = Multiset(
            {
                printing: -multiplicity
                for printing, multiplicity in self._cube_delta_operation.printings
                if multiplicity < 0
            }
        )

        new_nodes: Multiset[ConstrainedNode] = Multiset(
            {node: multiplicity for node, multiplicity in self._node_delta_operation.nodes.items() if multiplicity > 0}
        )

        removed_nodes: Multiset[ConstrainedNode] = Multiset(
            {
                node: -multiplicity
                for node, multiplicity in self._node_delta_operation.nodes.items()
                if multiplicity < 0
            }
        )

        new_printings_cardboard_map = defaultdict(lambda: [])

        for printing in new_printings:
            new_printings_cardboard_map[printing.cardboard].append(printing)

        removed_printings_cardboard_map = defaultdict(lambda: [])

        for printing in removed_printings:
            removed_printings_cardboard_map[printing.cardboard].append(printing)

        for printings in itertools.chain(
            new_printings_cardboard_map.values(),
            removed_printings_cardboard_map.values(),
        ):
            printings.sort(key=lambda p: p.expansion.code)

        printing_changes: Multiset[t.Tuple[Printing, Printing]] = Multiset()

        for cardboard in new_printings_cardboard_map.keys() & removed_printings_cardboard_map.keys():
            new = new_printings_cardboard_map[cardboard]
            removed = removed_printings_cardboard_map[cardboard]
            while new and removed:
                _new = new.pop()
                _removed = removed.pop()
                printing_changes.add((_removed, _new))
                new_printings.remove(_new, 1)
                removed_printings.remove(_removed, 1)

        new_unnested_nodes = sorted(
            (node for node in new_nodes if all(isinstance(child, Printing) for child in node.node.children)),
            key=lambda node: len(node.node.children),
            reverse=True,
        )

        printings_moved_to_nodes = Multiset()

        for node in new_unnested_nodes:
            if node.node.children <= removed_printings:
                printings_moved_to_nodes.add(
                    (
                        node.node.children,
                        node,
                    )
                )
                removed_printings -= node.node.children

        for _, node in printings_moved_to_nodes:
            new_nodes.remove(node, 1)

        removed_unnested_nodes = sorted(
            (node for node in removed_nodes if all(isinstance(child, Printing) for child in node.node.children)),
            key=lambda node: len(node.node.children),
            reverse=True,
        )

        nodes_moved_to_printings = Multiset()

        for node in removed_unnested_nodes:
            if node.node.children <= new_printings:
                nodes_moved_to_printings.add(
                    (
                        node.node.children,
                        node,
                    )
                )
                new_printings -= node.node.children

        for _, node in nodes_moved_to_printings:
            removed_nodes.remove(node, 1)

        removed_nodes_by_node: t.Dict[PrintingNode, t.List[ConstrainedNode]] = {}

        for node in removed_nodes:
            try:
                removed_nodes_by_node[node.node].append(node)
            except KeyError:
                removed_nodes_by_node[node.node] = [node]

        nodes_to_traps: Multiset[t.Tuple[Trap, ConstrainedNode]] = Multiset()

        for lap in new_laps:
            if isinstance(lap, Trap) and lap.node in removed_nodes_by_node:
                nodes_to_traps.add((lap, removed_nodes_by_node[lap.node].pop()))
                if not removed_nodes_by_node[lap.node]:
                    del removed_nodes_by_node[lap.node]

        for trap, node in nodes_to_traps:
            new_laps.remove(trap, 1)
            removed_nodes.remove(node, 1)

        new_nodes_by_node: t.Dict[PrintingNode, t.List[ConstrainedNode]] = {}

        for node in new_nodes:
            try:
                new_nodes_by_node[node.node].append(node)
            except KeyError:
                new_nodes_by_node[node.node] = [node]

        traps_to_nodes: Multiset[t.Tuple[Trap, ConstrainedNode]] = Multiset()

        for lap in removed_laps:
            if isinstance(lap, Trap) and lap.node in new_nodes_by_node:
                traps_to_nodes.add((lap, new_nodes_by_node[lap.node].pop()))
                if not new_nodes_by_node[lap.node]:
                    del new_nodes_by_node[lap.node]

        for trap, node in traps_to_nodes:
            removed_laps.remove(trap, 1)
            new_nodes.remove(node, 1)

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
                (AddInfinite(cardboard) for cardboard in self._infinites_delta_operation.added),
                (RemoveInfinite(cardboard) for cardboard in self._infinites_delta_operation.removed),
                group_updates,
                (PrintingChange(before, after) for before, after in printing_changes),
                (NewCubeable(lap) for lap in new_laps),
                (RemovedCubeable(lap) for lap in removed_laps),
                (NewCubeable(printing) for printing in new_printings),
                (RemovedCubeable(printing) for printing in removed_printings),
                (NewNode(node) for node in new_nodes),
                (RemovedNode(node) for node in removed_nodes),
                (PrintingsToNode(printings, node) for printings, node in printings_moved_to_nodes),
                (NodeToPrintings(node, printings) for printings, node in nodes_moved_to_printings),
                (NodeToTrap(trap, node) for trap, node in nodes_to_traps),
                (TrapToNode(trap, node) for trap, node in traps_to_nodes),
                (AlteredNode(before, after) for before, after in altered_nodes),
            )
        )

    def serialize(self) -> serialization_model:
        return {
            "cube_delta": self._cube_delta_operation,
            "nodes_delta": self._node_delta_operation,
            "groups_delta": self._group_map_delta_operation,
            "infinites_delta": self._infinites_delta_operation,
        }

    @classmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CubePatch:
        return cls(
            cube_delta_operation=CubeDeltaOperation.deserialize(value["cube_delta"], inflator),
            node_delta_operation=(
                NodesDeltaOperation.deserialize(value["nodes_delta"], inflator)
                if "nodes_delta" in value
                else NodesDeltaOperation()
            ),
            group_map_delta_operation=(
                GroupMapDeltaOperation.deserialize(value["groups_delta"], inflator)
                if "groups_delta" in value
                else GroupMapDeltaOperation()
            ),
            infinites_delta_operation=(
                InfinitesDeltaOperation.deserialize(value["infinites_delta"], inflator)
                if "infinites_delta" in value
                else InfinitesDeltaOperation()
            ),
        )

    def _calc_persistent_hash(self) -> t.Iterator[t.ByteString]:
        yield self._cube_delta_operation.persistent_hash().encode("ASCII")
        yield self._node_delta_operation.persistent_hash().encode("ASCII")
        yield self._group_map_delta_operation.persistent_hash().encode("ASCII")
        yield self._infinites_delta_operation.persistent_hash().encode("ASCII")

    def __hash__(self) -> int:
        return hash(
            (
                self._cube_delta_operation,
                self._node_delta_operation,
                self._group_map_delta_operation,
                self._infinites_delta_operation,
            )
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._cube_delta_operation == other._cube_delta_operation
            and self._node_delta_operation == other._node_delta_operation
            and self._group_map_delta_operation == other.group_map_delta_operation
            and self._infinites_delta_operation == other._infinites_delta_operation
        )

    def __repr__(self):
        return "{}({}, {}, {}, {})".format(
            self.__class__.__name__,
            self._cube_delta_operation,
            self._node_delta_operation,
            self._group_map_delta_operation,
            self._infinites_delta_operation,
        )

    def __mul__(self, other: int) -> CubePatch:
        return self.__class__(
            self._cube_delta_operation * other,
            self._node_delta_operation * other,
            self._group_map_delta_operation * other,
            self._infinites_delta_operation,
        )

    def __add__(self, other: t.Union[CubePatch, MetaCube]) -> t.Union[CubePatch, MetaCube]:
        if isinstance(other, MetaCube):
            return MetaCube(
                other.cube + self._cube_delta_operation,
                other.node_collection + self._node_delta_operation,
                other.group_map + self._group_map_delta_operation,
                other.infinites + self._infinites_delta_operation,
            )
        return self.__class__(
            self._cube_delta_operation + other._cube_delta_operation,
            self._node_delta_operation + other._node_delta_operation,
            self._group_map_delta_operation + other._group_map_delta_operation,
            self._infinites_delta_operation + other._infinites_delta_operation,
        )

    __radd__ = __add__

    def __sub__(self, other: CubePatch) -> CubePatch:
        return self.__class__(
            self._cube_delta_operation - other._cube_delta_operation,
            self._node_delta_operation - other._node_delta_operation,
            self._group_map_delta_operation - other._group_map_delta_operation,
            self._infinites_delta_operation - other._infinites_delta_operation,
        )


class CubeUpdater(object):
    def __init__(
        self,
        meta_cube: MetaCube,
        patch: CubePatch,
    ):
        self._meta_cube = meta_cube
        self._patch = patch

        self._new_cube: t.Optional[Cube] = None
        self._new_nodes: t.Optional[NodeCollection] = None
        self._new_groups: t.Optional[GroupMap] = None

        self._new_no_garbage_cube: t.Optional[Cube] = None
        self._new_nodes = None

    @property
    def meta_cube(self) -> MetaCube:
        return self._meta_cube

    @property
    def patch(self) -> CubePatch:
        return self._patch

    @property
    def cube(self) -> Cube:
        return self._meta_cube.cube

    @property
    def node_collection(self) -> NodeCollection:
        return self._meta_cube.node_collection

    @property
    def group_map(self) -> GroupMap:
        return self._meta_cube.group_map

    @property
    def new_cube(self) -> Cube:
        if self._new_cube is None:
            self._new_cube = self._meta_cube.cube + self._patch.cube_delta_operation
        return self._new_cube

    @property
    def new_nodes(self) -> NodeCollection:
        if self._new_nodes is None:
            self._new_nodes = self._meta_cube.node_collection + self._patch.node_delta_operation
        return self._new_nodes

    @property
    def new_groups(self) -> GroupMap:
        if self._new_groups is None:
            self._new_groups = self._meta_cube.group_map + self._patch.group_map_delta_operation
        return self._new_groups

    @property
    def new_infinites(self):
        return self._meta_cube.infinites + self._patch.infinites_delta_operation

    @property
    def new_no_garbage_cube(self) -> Cube:
        if self._new_no_garbage_cube is None:
            self._new_no_garbage_cube = (
                self.cube + ~CubeDeltaOperation(self.cube.garbage_traps.elements()) + self._patch.cube_delta_operation
            )

        return self._new_no_garbage_cube

    @property
    def new_garbage_trap_amount(self):
        return max(len(self.cube) - len(self.new_no_garbage_cube), 0)

    def old_average_trap_size(self) -> float:
        return len(self.node_collection) / len(self.cube.garbage_traps)

    def new_average_trap_size(self) -> float:
        return len(self.new_nodes) / self.new_garbage_trap_amount

    def get_finale_cube(self, new_garbage: t.Optional[TrapCollection]) -> Cube:
        if new_garbage is None:
            return self.new_cube
        else:
            return self.new_cube - Cube(self.new_cube.garbage_traps) + Cube(new_garbage)
