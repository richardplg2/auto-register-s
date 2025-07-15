import threading
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

import structlog

from app.workers.auto_register_serve_worker import AutoRegisterServeWorker
from app.workers.base_worker import BaseWorker
from app.workers.device_event_polling_worker import DeviceEventPollingWorker
from app.workers.event_polling_worker import EventPollingWorker
from app.workers.worker_types import WorkerType

if TYPE_CHECKING:
    from app.core.containers import Container


class WorkerInstance:
    id: UUID
    instance: BaseWorker
    device_code: Optional[str]

    worker_type: WorkerType

    started_at: datetime

    def __init__(
        self,
        instance: BaseWorker,
        worker_type: WorkerType,
        device_code: Optional[str] = None,
    ):
        self.id = uuid4()
        self.instance = instance
        self.device_code = device_code
        self.worker_type = worker_type
        self.started_at = datetime.now()

    def start(self):
        self.instance.start()

    def stop(self, timeout: Optional[float] = 30):
        self.instance.stop(timeout=timeout)


class WorkerManager:
    def __init__(
        self,
    ):
        self.container: "Container | None" = None
        self.lock = threading.Lock()
        self.worker_instances: list[WorkerInstance] = []
        self.running = False
        self.logger = structlog.get_logger(__name__)

    def init(self, container: "Container"):
        self.container = container
        # Pass container to workers that need it

        self.add_worker(WorkerType.MAIN, AutoRegisterServeWorker(container))
        self.add_worker(WorkerType.MAIN, EventPollingWorker())

    def add_worker(
        self,
        worker_type: WorkerType,
        worker: BaseWorker,
        device_code: Optional[str] = None,
    ) -> None:
        with self.lock:
            self.worker_instances.append(
                WorkerInstance(worker, worker_type, device_code)
            )

    def _init_instance_by_type(
        self, worker_type: WorkerType, device_code: Optional[str] = None
    ):
        if self.container is None:
            raise Exception("Container is not initialized")
        if worker_type == WorkerType.MAIN:
            return AutoRegisterServeWorker(self.container)
        elif (
            worker_type == WorkerType.DEVICE_EVENTS_POLLING and device_code is not None
        ):
            return DeviceEventPollingWorker(device_code, self.container)
        raise ValueError(f"Unknown worker type: {worker_type}")

    def _is_existed_device_worker(self, device_code: str, worker_type: WorkerType):
        with self.lock:
            for worker in self.worker_instances:
                if (
                    worker.device_code == device_code
                    and worker.worker_type == worker_type
                ):
                    return True
        return False

    def run_device_worker(self, device_code: str, worker_type: WorkerType) -> None:
        """Run a worker for a specific device."""
        if self.running == False:
            raise Exception("Worker manager is not running")

        if self._is_existed_device_worker(device_code, worker_type):
            self.logger.info(
                f"Device worker already exists: {device_code}, {worker_type}"
            )
            return

        instance = self._init_instance_by_type(worker_type, device_code)
        self.add_worker(
            worker_type,
            instance,
            device_code,
        )

        instance.start()

    def _get_worker_by_code_n_worker_type(
        self, device_code: str, worker_type: WorkerType
    ):
        for worker in self.worker_instances:
            if worker.device_code == device_code and worker.worker_type == worker_type:
                return worker
        return None

    def stop_device_worker(self, device_code: str, worker_type: WorkerType) -> None:
        """Stop a worker for a specific device."""
        if self.running == False:
            raise Exception("Worker manager is not running")

        worker = self._get_worker_by_code_n_worker_type(device_code, worker_type)
        if worker:
            worker.stop()

            with self.lock:
                self.worker_instances.remove(worker)

            self.logger.info(
                f"Stopped device worker: {device_code}, {worker_type}, remaining: {len(self.worker_instances)}"
            )
        else:
            self.logger.warn(f"Device worker not found: {device_code}, {worker_type}")

    def start_all(self) -> None:
        """Start all workers in separate threads"""
        for worker in self.worker_instances:
            worker.start()  # Only call start(), not run()

        self.running = True

    def stop_all(self, timeout: Optional[float] = 30) -> None:
        for worker in self.worker_instances:
            worker.stop(timeout=timeout)

        self.running = False
