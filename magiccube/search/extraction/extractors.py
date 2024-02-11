from __future__ import annotations

import typing as t
from abc import ABCMeta

from mtgorp.models.interfaces import Printing
from mtgorp.tools.search.extraction import (
    CardboardStrategy,
    ExtractionStrategy,
    PrintingStrategy,
    T,
)

from magiccube.collections.cubeable import CardboardCubeable, Cubeable
from magiccube.laps.traps.trap import Trap


def _get_strategy_wrapper(base_strategy: t.Type[ExtractionStrategy]) -> t.Type:
    class _CubeableExtractionStrategyMeta(ABCMeta):
        @classmethod
        def _wrap(
            mcs,
            f: t.Callable[[T], t.Iterable[t.Any]],
        ) -> t.Callable[[T], t.Iterable[t.Any]]:
            def _wrapped(extractable: T) -> t.Iterable[t.Any]:
                if isinstance(extractable, Printing):
                    yield from f(extractable)
                if isinstance(extractable, Trap):
                    for p in extractable:
                        yield from f(p)
                else:
                    return ()

            return _wrapped

        def __new__(mcs, name, bases, namespace, **kwargs):
            for k in bases[-1].__dict__:
                if k.startswith("extract"):
                    namespace[k] = mcs._wrap(getattr(base_strategy, k))
            return super().__new__(mcs, name, bases, namespace, **kwargs)

    return _CubeableExtractionStrategyMeta


class CubeableStrategy(
    ExtractionStrategy[Cubeable],
    metaclass=_get_strategy_wrapper(PrintingStrategy),
):
    pass


class CardboardCubeableStrategy(
    ExtractionStrategy[CardboardCubeable],
    metaclass=_get_strategy_wrapper(CardboardStrategy),
):
    pass
