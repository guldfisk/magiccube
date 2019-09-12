from __future__ import annotations

import typing as t

import threading
import queue

from evolution.logging import LogFrame
from magiccube.laps.traps.distribute.algorithm import Distributor


class DistributionWorker(threading.Thread):

    def __init__(self, distributor: Distributor, *, max_generations: int = 0, **kwargs):
        super().__init__(**kwargs)
        self._distributor: Distributor = distributor
        self._max_generations = max_generations

        self._running: bool = False
        self._terminating = threading.Event()
        self._pause_lock = threading.Lock()
        self._communication_lock = threading.Lock()
        self._message_queue = queue.Queue()

    @property
    def message_queue(self) -> queue.Queue[t.Dict[str, t.Any]]:
        return self._message_queue

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


class DistributionTask(threading.Thread):

    def __init__(self, distributor: Distributor, max_generations: int = 0, **kwargs):
        super().__init__(**kwargs)
        self._worker = DistributionWorker(distributor, max_generations = max_generations)

        self._running: bool = False
        self._terminating = threading.Event()
        self._frame_lock = threading.Lock()
        self._message_queue = queue.Queue()

        self._communication_lock = threading.Lock()
        self._subscription_lock = threading.Lock()
        self._messages = []
        self._frames: t.List[LogFrame] = []
        self._subscribers: t.Dict[str, queue.Queue[t.Dict[str, t.Any]]] = {}

    @property
    def frames(self) -> t.List[LogFrame]:
        with self._frame_lock:
            return self._frames

    def _process_message(self, message: t.Dict[str, t.Any]) -> None:
        with self._subscription_lock:
            self._messages.append(message)
            for subscriber in self._subscribers.values():
                subscriber.put(message)

    def subscribe(self, key: str) -> queue.Queue[t.Dict[str, t.Any]]:
        with self._subscription_lock:
            q = queue.Queue()
            self._subscribers[key] = q
            q.put(
                {
                    'type': 'previous_messages',
                    'messages': self._messages,
                }
            )
            return q

    def unsubscribe(self, key: str) -> None:
        with self._subscription_lock:
            try:
                del self._subscribers[key]
            except KeyError:
                pass

    def stop(self):
        self._terminating.set()
        self._worker.stop()

    def pause(self):
        self._worker.pause()

    def resume(self):
        self._worker.resume()

    def run(self) -> None:
        self._worker.start()
        while True:
            try:
                message = self._worker.message_queue.get(timeout = 5)
                self._process_message(
                    message
                )
                if message['type'] == 'frame':
                    with self._frame_lock:
                        self._frames.append(message['frame'])
                if message['type'] == 'status' and message['status'] == 'stopped':
                    self._terminating.set()
            except queue.Empty:
                if self._terminating.is_set():
                    break
