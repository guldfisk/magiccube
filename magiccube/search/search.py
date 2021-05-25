import typing as t

from mtgorp.models.interfaces import Printing
from mtgorp.tools.search.pattern import PrintingPattern

from magiccube.collections.cubeable import Cubeable
from magiccube.laps.traps.trap import Trap


def match_cubeable(pattern: PrintingPattern, cubeables: t.Iterable[Cubeable]) -> t.Iterable[Cubeable]:
    for cubeable in cubeables:
        if isinstance(cubeable, Trap):
            if any(pattern.match(p) for p in cubeable):
                yield cubeable
        elif isinstance(cubeable, Printing) and pattern.match(cubeable):
            yield cubeable
