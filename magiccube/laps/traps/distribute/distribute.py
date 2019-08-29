from __future__ import annotations

import typing as t

import threading
import queue

from evolution.logging import LogFrame

from magiccube.laps.traps.distribute.algorithm import Distributor


class DistributionWorker(threading.Thread):

    def __init__(self, distributor: Distributor, **kwargs):
        super().__init__(**kwargs)
        self._distributor: Distributor = distributor
        
        self._running: bool = False
        self._terminating = threading.Event()
        self._pause_lock = threading.Lock()
        self._communication_lock = threading.Lock()
        self._message_queue = queue.Queue()

        self._log_frames = queue.Queue()

    @property
    def log_frames(self) -> queue.Queue[LogFrame]:
        return self._log_frames

    def stop(self):
        with self._communication_lock:
            self._running = False
            self._terminating.set()
            self._pause_lock.release()

    def pause(self):
        with self._communication_lock:
            self._pause_lock.acquire(blocking = False)
            self._running = False

    def resume(self):
        with self._communication_lock:
            self._pause_lock.release()
            self._running = True

    def run(self) -> None:
        self._running = True
        while not self._terminating.is_set():
            self._pause_lock.acquire()
            while self._running:
                self._log_frames.put(
                    self._distributor.spawn_generation()
                )

                
class DistributionTask(threading.Thread):

    def __init__(self, distributor: Distributor, **kwargs):
        super().__init__(**kwargs)
        self._worker = DistributionWorker(distributor, daemon = True)
        
        self._running: bool = False
        self._terminating = threading.Event()
        self._lock = threading.Lock()
        self._message_queue = queue.Queue()
        
        self._communication_lock = threading.Lock()
        self._subscription_lock = threading.Lock()
        self._frames = []
        self._subscribers: t.Dict[str, queue.Queue[t.Dict[str, t.Any]]] = {}
        
    def _process_frame(self, frame: LogFrame) -> None:
        with self._subscription_lock:
            self._frames.append(frame)
            for subscriber in self._subscribers.values():
                subscriber.put(
                    {
                        'type': 'frame',
                        'frame': frame,
                    }
                )
        
    def _notify_status_change(self, status: str) -> None:
        with self._subscription_lock:
            for subscriber in self._subscribers.values():
                subscriber.put(
                    {
                        'type': 'status_change',
                        'status': status,
                    }
                )

    def subscribe(self, key: str) -> queue.Queue[t.Dict[str, t.Any]]:
        with self._subscription_lock:
            q = queue.Queue()
            self._subscribers[key] = q
            q.put(
                {
                    'type': 'frames',
                    'frames': self._frames,
                }
            )
            return q

    def stop(self):
        self._terminating.set()
        self._worker.stop()
        self._notify_status_change('stopped')

    def pause(self):
        self._worker.pause()
        self._notify_status_change('paused')

    def resume(self):
        self._worker.resume()
        self._notify_status_change('resumed')
        

    def run(self) -> None:
        self._notify_status_change('started')
        self._worker.start()
        while not self._terminating.is_set():
            try:
                self._process_frame(
                    self._worker.log_frames.get(timeout = 5)
                )
            except queue.Empty:
                pass
