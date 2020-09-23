from __future__ import annotations

import typing as t

import threading
import queue
import math

from abc import ABC, abstractmethod

from evolution.environment import Environment
from evolution.logging import FitnessLoggingOperation


E = t.TypeVar('E', bound = Environment)


class AutoPauseCheck(ABC):

    @abstractmethod
    def check(self, worker: DistributionWorker) -> bool:
        pass

    @abstractmethod
    def resume(self, worker: DistributionWorker) -> None:
        pass


class GenerationAmountAutoPause(AutoPauseCheck):

    def __init__(self, generations: int, backoff: t.Optional[int] = None):
        self._generations = generations
        self._backoff = int(math.ceil(generations / 10)) if backoff is None else backoff

    def check(self, worker: DistributionWorker) -> bool:
        return len(worker.distributor.logger.values) >= self._generations

    def resume(self, worker: DistributionWorker) -> None:
        self._generations += self._backoff


class FitnessDifferentialAutoPause(AutoPauseCheck):

    def __init__(
        self,
        threshold: float,
        logging_operator: t.Type[FitnessLoggingOperation],
        backoff: float = .7,
        *,
        generations_lookback: int = 100,
    ):
        self._threshold = threshold
        self._logging_operator_type = logging_operator
        self._backoff = backoff
        self._generations_lookback = generations_lookback

    def check(self, worker: DistributionWorker) -> bool:
        if len(worker.distributor.logger.values) < self._generations_lookback:
            return False

        operation_index = None
        for idx, operation in enumerate(worker.distributor.logger.operations.values()):
            if isinstance(operation, self._logging_operator_type):
                operation_index = idx
                break
        if operation_index is None:
            raise ValueError('Invalid logging operator')

        return (
                   worker.distributor.logger.values[-1][operation_index]
                   - worker.distributor.logger.values[-self._generations_lookback][operation_index]
               ) / self._generations_lookback < self._threshold

    def resume(self, worker: DistributionWorker) -> None:
        self._threshold *= self._backoffgatherer


class DistributionWorker(threading.Thread, t.Generic[E]):

    def __init__(
        self,
        distributor: E,
        *,
        pause_conditions: t.Iterable[AutoPauseCheck] = (),
        max_generations: int = 0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._distributor: E = distributor
        self._max_generations = max_generations
        self._pause_conditions = pause_conditions

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
            for condition in self._pause_conditions:
                condition.resume(self)

    def run(self) -> None:
        self._running = True

        while not self._terminating.is_set():
            self._pause_lock.acquire()

            if self._running:
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

                if any(condition.check(self) for condition in self._pause_conditions):
                    self.pause()

            if not self._running and not self._terminating.is_set():
                self._notify_status('paused')

        self._notify_status('stopped')
