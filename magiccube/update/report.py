from __future__ import annotations

import typing as t
import itertools

from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict

from magiccube.collections.cube import Cube
from magiccube.collections.cubeable import Cubeable
from magiccube.collections.delta import CubeDelta
from magiccube.laps.traps.trap import Trap, IntentionType
from yeetlong.multiset import FrozenMultiset
from yeetlong.counters import FrozenCounter

from magiccube.collections.nodecollection import ConstrainedNode
from mtgorp.models.persistent.cardboard import Cardboard
from mtgorp.models.persistent.printing import Printing

from magiccube.update.cubeupdate import CubeUpdater


class ReportNotificationLevel(Enum):
    INFO = 'info'
    WARNING = 'warning'


class ReportNotification(ABC):
    notification_level = ReportNotificationLevel.INFO

    @classmethod
    @abstractmethod
    def check(cls, updater: CubeUpdater) -> t.Optional[ReportNotification]:
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        pass

    @property
    @abstractmethod
    def content(self) -> str:
        pass


class ChangedSize(ReportNotification):
    notification_level = ReportNotificationLevel.WARNING

    def __init__(self, original_size: int, size_delta: int):
        self._original_size = original_size
        self._size_delta = size_delta

    @classmethod
    def check(cls, updater: CubeUpdater) -> t.Optional[ChangedSize]:
        new_cube = updater.cube + updater.patch.cube_delta_operation

        size_delta = len(new_cube) - len(updater.cube)
        if size_delta == 0:
            return None

        return ChangedSize(
            len(updater.cube.cubeables),
            size_delta,
        )

    @property
    def title(self) -> str:
        return 'Cube changed size'

    @property
    def content(self) -> str:
        return 'Cube changed size from {} to {} ({})'.format(
            self._original_size,
            self._original_size + self._size_delta,
            ('+' if self._size_delta > 0 else '') + str(self._size_delta)
        )


class NodesWithoutGroups(ReportNotification):
    notification_level = ReportNotificationLevel.WARNING

    def __init__(self, nodes: FrozenMultiset[ConstrainedNode]):
        self._nodes = nodes

    @classmethod
    def check(cls, updater: CubeUpdater) -> t.Optional[NodesWithoutGroups]:
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

    @property
    def title(self) -> str:
        return 'New nodes without groups'

    @property
    def content(self) -> str:
        return 'Added the following nodes without any groups:\n' + (
            '\n'.join(
                ((str(multiplicity) + 'x ') if multiplicity != 1 else '') + node.get_minimal_string()
                for node, multiplicity in
                self._nodes.items()
            )
        )


# class NewGroupsWithoutNodes(ReportNotification):
#     notification_level = ReportNotificationLevel.WARNING
# 
#     @classmethod
#     def check(cls, updater: CubeUpdater) -> t.Optional[ReportNotification]:
#         pass
# 
#     @property
#     def title(self) -> str:
#         pass
# 
#     @property
#     def content(self) -> str:
#         pass


# class NodesWithUnknownGroups(ReportNotification):
#     notification_level = ReportNotificationLevel.WARNING
# 
#     @classmethod
#     def check(cls, updater: CubeUpdater) -> t.Optional[ReportNotification]:
#         pass
# 
#     @property
#     def title(self) -> str:
#         pass
# 
#     @property
#     def content(self) -> str:
#         pass


class RemoveNonExistentCubeables(ReportNotification):
    notification_level = ReportNotificationLevel.WARNING

    def __init__(self, non_existent_removed_cubeables: FrozenMultiset[Cubeable]):
        self._non_existent_removed_cubeables = Cube(non_existent_removed_cubeables)

    @classmethod
    def check(cls, updater: CubeUpdater) -> t.Optional[ReportNotification]:
        non_existent_cuts = FrozenMultiset(
            {
                cubeable: multiplicity
                for cubeable, multiplicity in
                (~updater.patch.cube_delta_operation.cubeables).positive()
            }
        ) - updater.cube.cubeables

        if non_existent_cuts:
            return cls(non_existent_cuts)
        else:
            return None

    @property
    def title(self) -> str:
        return 'Remove non-existent cubeables'

    @property
    def content(self) -> str:
        return self._non_existent_removed_cubeables.pp_string


class PrintingMismatch(ReportNotification):
    notification_level = ReportNotificationLevel.WARNING

    def __init__(self, mismatches: t.Dict[Cardboard, t.Tuple[t.AbstractSet[Printing], t.AbstractSet[Printing]]]):
        self._mismatches = mismatches

    @classmethod
    def check(cls, updater: CubeUpdater) -> t.Optional[PrintingMismatch]:
        old_cardboard_map = defaultdict(lambda: set())
        for printing in updater.cube.all_printings:
            old_cardboard_map[printing.cardboard].add(printing)

        new_cardboard_map = defaultdict(lambda: set())
        for printing in itertools.chain(
            updater.patch.cube_delta_operation.all_new_printings,
            updater.patch.node_delta_operation.all_new_printings,
        ):
            new_cardboard_map[printing.cardboard].add(printing)

        mismatches = {
            key: (
                new_cardboard_map[key] - old_cardboard_map[key],
                old_cardboard_map[key],
            )
            for key in
            old_cardboard_map.keys() & new_cardboard_map.keys()
            if new_cardboard_map[key] - old_cardboard_map[key]
        }

        if not mismatches:
            return None

        return PrintingMismatch(
            mismatches
        )

    @property
    def title(self) -> str:
        return 'New printings mismatch'

    @property
    def content(self) -> str:
        return 'The following is printings added that share cardboard, but not printing, with existing printings:\n' + (
            '\n'.join(
                '{}: {} : {}'.format(
                    cardboard.name,
                    ', '.join(sorted((printing.expansion.code for printing in values[0]))),
                    ', '.join(sorted((printing.expansion.code for printing in values[1]))),
                )
                for cardboard, values in
                sorted(
                    self._mismatches.items(),
                    key = lambda i: i[0].name,
                )
            )
        )


class TrapSize(ReportNotification):
    notification_level = ReportNotificationLevel.INFO

    def __init__(self, old_trap_amount, old_node_amount, new_trap_amount, new_node_amount):
        self._old_trap_amount = old_trap_amount
        self._old_node_amount = old_node_amount
        self._new_trap_amount = new_trap_amount
        self._new_node_amount = new_node_amount

    @classmethod
    def check(cls, updater: CubeUpdater) -> t.Optional[ReportNotification]:
        return cls(
            old_trap_amount = len(updater.cube.garbage_traps),
            old_node_amount = len(updater.node_collection),
            new_trap_amount = updater.new_garbage_trap_amount,
            new_node_amount = len(updater.node_collection + updater.patch.node_delta_operation),
        )

    @property
    def title(self) -> str:
        return 'Trap sizes'

    @property
    def content(self) -> str:
        return 'Old average node pr trap: {} ({} / {})\nNew average node pr trap: {} ({} / {})'.format(
            round(self._old_node_amount / self._old_trap_amount, 2),
            self._old_node_amount,
            self._old_trap_amount,
            round(self._new_node_amount / self._new_trap_amount, 2),
            self._new_node_amount,
            self._new_trap_amount,
        )


class CardboardChange(ReportNotification):
    notification_level = ReportNotificationLevel.INFO

    def __init__(self, changes: FrozenCounter[Cardboard]):
        self._changes = changes

    @classmethod
    def check(cls, updater: CubeUpdater) -> t.Optional[ReportNotification]:
        non_garbage_cube = Cube(
            (
                cubeable
                for cubeable in
                updater.cube.cubeables
                if not (
                    isinstance(cubeable, Trap)
                    and cubeable.intention_type == IntentionType.GARBAGE
                )
            )
        )
        
        new_no_garbage_cube = Cube(
            (
                cubeable
                for cubeable in
                (updater.cube + updater.patch.cube_delta_operation).cubeables
                if not (
                    isinstance(cubeable, Trap)
                    and cubeable.intention_type == IntentionType.GARBAGE
                )
            )
        )
        
        old_cardboards = FrozenMultiset(
            printing.cardboard
            for printing in
            itertools.chain(
                non_garbage_cube.all_printings,
                updater.node_collection.all_printings,
            )
        )
        
        new_cardboards = FrozenMultiset(
            printing.cardboard
            for printing in
            itertools.chain(
                new_no_garbage_cube.all_printings,
                (updater.node_collection + updater.patch.node_delta_operation).all_printings,
            )
        )
        
        return CardboardChange(
            FrozenCounter(
                new_cardboards.elements()
            ) - FrozenCounter(
                old_cardboards.elements()
            )
        )

    @property
    def title(self) -> str:
        return 'Cardboard changes'

    @property
    def content(self) -> str:
        return 'Added:\n{}\n\nRemoved:\n{}'.format(
            '\n'.join(
                ((str(multiplicity) + 'x ') if multiplicity != 1 else '') + cardboard.name
                for cardboard, multiplicity in
                self._changes.items()
                if multiplicity > 0
            ),
            '\n'.join(
                str(multiplicity) + ' ' + cardboard.name
                for cardboard, multiplicity in
                self._changes.items()
                if multiplicity < 0
            ),
        )


class ReportBlueprint(object):

    def __init__(self, notification_checks: t.Iterable[t.Type[ReportNotification]]):
        self._notification_checks = (
            notification_checks
            if isinstance(notification_checks, set) else
            set(notification_checks)
        )

    @property
    def checks(self) -> t.AbstractSet[t.Type[ReportNotification]]:
        return self._notification_checks

    def __hash__(self) -> int:
        return hash(self._notification_checks)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, self.__class__)
            and self._notification_checks == other._notification_checks
        )


DEFAULT_REPORT_BLUEPRINT = ReportBlueprint(
    {
        # Warnings
        ChangedSize,
        NodesWithoutGroups,
        RemoveNonExistentCubeables,
        PrintingMismatch,
        # Info
        TrapSize,
        CardboardChange,
    }
)


class UpdateReport(object):

    def __init__(self, updater: CubeUpdater, blueprint: ReportBlueprint = DEFAULT_REPORT_BLUEPRINT):
        self._updater = updater
        self._blueprint = blueprint

        self._notifications = sorted(
            (
                notification
                for notification in
                (
                    check.check(
                        self._updater,
                    )
                    for check in
                    self._blueprint.checks
                )
                if notification
            ),
            key = lambda n: n.title,
        )

    @property
    def warnings(self) -> t.Iterator[ReportNotification]:
        return (
            notification
            for notification in
            self._notifications
            if notification.notification_level == ReportNotificationLevel.WARNING
        )

    @property
    def infos(self) -> t.Iterator[ReportNotification]:
        return (
            notification
            for notification in
            self._notifications
            if notification.notification_level == ReportNotificationLevel.INFO
        )

    @property
    def notifications(self) -> t.Iterator[ReportNotification]:
        return itertools.chain(
            self.warnings,
            self.infos,
        )
