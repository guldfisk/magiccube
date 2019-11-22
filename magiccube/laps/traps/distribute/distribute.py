from __future__ import annotations

import typing as t

import threading
import queue

from evolution.environment import Environment


E = t.TypeVar('E', bound = Environment)


class DistributionWorker(threading.Thread, t.Generic[E]):

    def __init__(self, distributor: E, *, max_generations: int = 0, **kwargs):
        super().__init__(**kwargs)
        self._distributor: E = distributor
        self._max_generations = max_generations

        self._running: bool = False
        self._terminating = threading.Event()
        self._pause_lock = threading.Lock()
        self._communication_lock = threading.Lock()
        self._message_queue = queue.Queue()

    @property
    def message_queue(self) -> queue.Queue[t.Dict[str, t.Any]]:
        return self._message_queue

    @property
    def distributor(self) -> E:
        # UNSAFE
        return self._distributor

    def _notify_status(self, status: str) -> None:
        self._message_queue.put(
            {
                'type': 'status',
                'status': status,
            }
        )

    def stop(self):
        if self._terminating.is_set():
            return
        with self._communication_lock:
            self._notify_status('stopping')
            self._running = False
            self._terminating.set()
            try:
                self._pause_lock.release()
            except RuntimeError:
                pass

    def pause(self):
        if self._terminating.is_set():
            return
        with self._communication_lock:
            if not self._running:
                return
            self._notify_status('pausing')
            self._pause_lock.acquire(blocking = False)
            self._running = False

    def resume(self):
        if self._terminating.is_set():
            return
        with self._communication_lock:
            if self._running:
                return
            self._notify_status('resuming')
            try:
                self._pause_lock.release()
            except RuntimeError:
                pass
            self._running = True

    def run(self) -> None:
        self._running = True
        while not self._terminating.is_set():
            self._pause_lock.acquire()
            self._notify_status('running')
            while self._running:
                self._message_queue.put(
                    {
                        'type': 'frame',
                        'frame': self._distributor.spawn_generation(),
                    }
                )
                if (
                    self._max_generations
                    and len(self._distributor.logger.values) >= self._max_generations
                ):
                    self._message_queue.put(
                        {
                            'type': 'status',
                            'status': 'completed',
                            'generations': len(self._distributor.logger.values)
                        }
                    )
                    self.stop()
            if not self._running and not self._terminating.is_set():
                self._notify_status('paused')
        self._notify_status('stopped')

