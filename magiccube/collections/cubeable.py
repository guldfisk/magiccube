from __future__ import annotations

import json
import typing as t
import re

from abc import abstractmethod

from mtgorp.models.persistent.printing import Printing
from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator
from mtgorp.models.serilization.strategies.jsonid import JsonId
from mtgorp.models.serilization.strategies.raw import RawStrategy

from magiccube.laps.purples.purple import Purple
from magiccube.laps.tickets.ticket import Ticket
from magiccube.laps.traps.trap import Trap
from magiccube.laps.lap import Lap


Cubeable = t.Union[Lap, Printing]

LAP_NAME_MAP = {
    'Trap': Trap,
    'Ticket': Ticket,
    'Purple': Purple,
}

_PRINTING_ID_PATTERN = re.compile('\d')


def serialize_cubeable(cubeable: Cubeable) -> t.Any:
    return cubeable.id if isinstance(cubeable, Printing) else RawStrategy.serialize(cubeable)


def serialize_cubeable_string(cubeable: Cubeable) -> t.Any:
    return str(cubeable.id) if isinstance(cubeable, Printing) else JsonId.serialize(cubeable)


def deserialize_cubeable(cubeable: serialization_model, inflator: Inflator) -> Cubeable:
    return (
        inflator.inflate(Printing, cubeable)
        if isinstance(cubeable, int) else
        LAP_NAME_MAP[cubeable['type']].deserialize(cubeable, inflator)
    )


def deserialize_cubeable_string(cubeable: str, inflator: Inflator) -> Cubeable:
    if _PRINTING_ID_PATTERN.match(cubeable):
        return inflator.inflate(Printing, int(cubeable))
    else:
        cubeable = json.loads(cubeable)
        return LAP_NAME_MAP[cubeable['type']].deserialize(cubeable, inflator)


class CubeableCollection(Serializeable):

    @property
    @abstractmethod
    def cubeables(self) -> t.Iterable[Cubeable]:
        pass

    @abstractmethod
    def serialize(self) -> serialization_model:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, value: serialization_model, inflator: Inflator) -> CubeableCollection:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass
