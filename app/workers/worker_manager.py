from typing import Optional

from app.core.containers import Container
from app.workers.auto_register_serve_worker import AutoRegisterServeWorker
from app.workers.base_worker import BaseWorker
from app.workers.event_polling_worker import EventPollingWorker


class WorkerManager:
    def __init__(self, container: Container):
        self.workers: list[BaseWorker] = []
        self.container = container

        # Pass container to workers that need it
        w1 = AutoRegisterServeWorker(container)
        w2 = EventPollingWorker()

        self.add_worker(w1)
        self.add_worker(w2)

    def add_worker(self, worker: BaseWorker) -> None:
        self.workers.append(worker)

    def start_all(self) -> None:
        """Start all workers in separate threads"""
        for worker in self.workers:
            worker.start()  # Only call start(), not run()

    def stop_all(self, timeout: Optional[float] = 30) -> None:
        for worker in self.workers:
            worker.stop(timeout=timeout)
