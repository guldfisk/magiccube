import typing as t

import threading
import queue

from promise import Promise

from proxypdf.write import save_proxy_pdf

from mtgimg.load import Loader as ImageLoader

from magiccube.laps.lap import Lap
from magiccube.laps.traps.distribute.algorithm import Distributor


def proxy_laps(
    laps: t.Iterable[Lap],
    image_loader: ImageLoader,
    file: t.Union[t.BinaryIO, str],
    margin_size: float = .1,
    card_margin_size: float = .01,
) -> None:
    save_proxy_pdf(
        file = file,
        images = Promise.all(
            tuple(
                image_loader.get_image(lap, save = False)
                for lap in
                laps
            )
        ).get(),
        margin_size = margin_size,
        card_margin_size = card_margin_size,
    )


class DistributionTask(threading.Thread):

    def __init__(self, distributor: Distributor):
        super().__init__()
        self._distributor: Distributor = distributor
        self._started: bool = False
        self._running: bool = False
        self._lock = threading.Lock()
        self._message_queue = queue.Queue()

    def run(self) -> None:
        self._started = True
        self._running = True
        while self._started:
            self._lock.acquire()

