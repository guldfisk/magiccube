from __future__ import annotations

import json
import typing as t
import re

from abc import abstractmethod

from mtgorp.models.interfaces import Printing, Cardboard
from mtgorp.models.serilization.serializeable import Serializeable, serialization_model, Inflator
from mtgorp.models.serilization.strategies.jsonid import JsonId
from mtgorp.models.serilization.strategies.raw import RawStrategy

from magiccube.laps.purples.purple import Purple, CardboardPurple
from magiccube.laps.tickets.ticket import Ticket, CardboardTicket
from magiccube.laps.traps.trap import Trap, CardboardTrap
from magiccube.laps.lap import Lap, CardboardLap


Cubeable = t.Union[Lap, Printing]
CardboardCubeable = t.Union[CardboardLap, Cardboard]
BaseCubeable = t.Union[Cubeable, CardboardCubeable]

LAP_NAME_MAP = {
    'Trap': Trap,
    'Ticket': Ticket,
    'Purple': Purple,
}

CARDBOARD_LAP_NAME_MAP = {
    'CardboardTrap': CardboardTrap,
    'CardboardTicket': CardboardTicket,
    'CardboardPurple': CardboardPurple,
}

_PRINTING_ID_PATTERN = re.compile('\d')


def serialize_cubeable(cubeable: Cubeable) -> t.Any:
    return cubeable.id if isinstance(cubeable, Printing) else RawStrategy.serialize(cubeable)


def serialize_cardboard_cubeable(cardboard_cubeable: CardboardCubeable) -> t.Any:
    return cardboard_cubeable.name if isinstance(cardboard_cubeable, Cardboard) else RawStrategy.serialize(
        cardboard_cubeable)


def serialize_cubeable_string(cubeable: Cubeable) -> t.Any:
    return str(cubeable.id) if isinstance(cubeable, Printing) else JsonId.serialize(cubeable)


def serialize_cardboard_cubeable_string(cardboard_cubeable: CardboardCubeable) -> t.Any:
    return cardboard_cubeable.name if isinstance(cardboard_cubeable, Cardboard) else JsonId.serialize(
        cardboard_cubeable)


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


def deserialize_cardboard_cubeable_string(cardboard_cubeable: str, inflator: Inflator) -> CardboardCubeable:
    if cardboard_cubeable.startswith('{'):
        cardboard_cubeable = json.loads(cardboard_cubeable)
        return CARDBOARD_LAP_NAME_MAP[cardboard_cubeable['type']].deserialize(cardboard_cubeable, inflator)

    return inflator.inflate(Cardboard, cardboard_cubeable)


def cardboardize(cubeable: Cubeable) -> CardboardCubeable:
    if isinstance(cubeable, Printing):
        return cubeable.cardboard
    return cubeable.as_cardboards


class BaseCubeableCollection(Serializeable):

    @property
    @abstractmethod
    def items(self) -> t.Iterable[BaseCubeable]:
        pass


class CardboardCubeableCollection(BaseCubeableCollection):

    @property
    @abstractmethod
    def cardboard_cubeables(self) -> t.Iterable[CardboardCubeable]:
        pass


class CubeableCollection(BaseCubeableCollection):

    @property
    @abstractmethod
    def cubeables(self) -> t.Iterable[Cubeable]:
        pass
