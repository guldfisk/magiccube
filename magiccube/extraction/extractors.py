from __future__ import annotations

import typing as t

from abc import ABCMeta

from mtgorp.models.persistent.printing import Printing
from mtgorp.tools.search.extraction import ExtractionStrategy, T, PrintingStrategy

from magiccube.laps.lap import Lap


class _CubeableExtractionStrategyMeta(ABCMeta):

    @classmethod
    def _wrap(
            mcs,
            f: t.Callable[[T], t.Iterable[t.Any]],
    ) -> t.Callable[[T], t.Iterable[t.Any]]:
        def _wrapped(extractable: T) -> t.Iterable[t.Any]:
            if isinstance(extractable, Printing):
                return f(extractable)
            return ()

        return _wrapped

    def __new__(mcs, name, bases, namespace, **kwargs):
        for k in bases[-1].__dict__:
            if k.startswith('extract'):
                namespace[k] = mcs._wrap(
                    getattr(PrintingStrategy, k)
                )
        return super().__new__(mcs, name, bases, namespace, **kwargs)


class CubeableStrategy(
    ExtractionStrategy[t.Union[Printing, Lap]],
    metaclass = _CubeableExtractionStrategyMeta,
):
    pass
