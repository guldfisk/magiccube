import typing as t

from mtgorp.models.serilization.serializeable import compacted_model
from mtgorp.models.serilization.strategies.strategy import Strategy



class CubeParseStrategy(Strategy):

    @classmethod
    def _serialize(cls, model: compacted_model) -> t.AnyStr:
        pass

    def _deserialize(self, s: t.AnyStr) -> compacted_model:
        pass