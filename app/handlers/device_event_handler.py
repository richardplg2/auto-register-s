from datetime import datetime
from typing import Any

import structlog
from NetSDK.SDK_Enum import EM_AUTOREGISTER_TYPE  # type: ignore

from app.core.event_bus import Event, EventHandler
from app.repos.device_repo import DeviceRepo
from app.services.dahua_netsdk_service import DahuaNetSDKService
from app.workers.worker_manager import WorkerManager
from app.workers.worker_types import WorkerType

logger = structlog.get_logger(__name__)


class DeviceAutoRegisterHandler(EventHandler):
    """Handler for device auto register events"""

    def __init__(
        self,
        device_repo: DeviceRepo,
        dahua_netsdk_service: DahuaNetSDKService,
        worker_manager: WorkerManager,
    ):
        self.device_repo = device_repo
        self.dahua_netsdk_service = dahua_netsdk_service
        self.worker_manager = worker_manager

    async def handle(self, event: Event) -> None:
        """Handle device auto register event"""
        if event.event_type != "device_auto_register":
            return

        try:
            device_code = event.data["device_code"]
            ip = event.data["ip"]
            port = event.data["port"]
            command = event.data["command"]

            logger.info(
                "Processing device auto register event",
                device_code=device_code,
                ip=ip,
                port=port,
                command=command,
                source_thread=event.source_thread,
            )

            # Get device by code
            device = await self.device_repo.get_by_code(device_code)
            if device is None or device.is_active is False:
                logger.info(
                    "Device is not registered or inactive", device_code=device_code
                )
                return

            # Update device status based on command
            if command == EM_AUTOREGISTER_TYPE.DISCONNECT:
                logger.info("Device is disconnected", device_code=device_code)
                updates: dict[Any, Any] = {
                    "is_online": False,
                    "last_disconnected_at": datetime.now(),
                }
                await self.device_repo.update_device_by_code(device_code, updates)

                # Stop dynamic worker for polling events
                self.worker_manager.stop_device_worker(
                    device_code, WorkerType.DEVICE_EVENTS_POLLING
                )
                return

            if device.username is None or device.password is None:
                logger.error(
                    "Device username or password is not set", device_code=device_code
                )
                return

            logger.info("Device is connected", device_code=device_code)

            login_id = self.dahua_netsdk_service.login(
                device_code, ip, port, device.username, device.password
            )

            print(f"Login ID: {login_id}")

            updates: dict[Any, Any] = {
                "is_online": login_id > 0,
                "last_connected_at": datetime.now(),
                "ip": ip,
                "port": port,
            }

            # Update device using async repo
            await self.device_repo.update_device_by_code(device_code, updates)

            logger.info(
                "Device status updated successfully",
                device_code=device_code,
                updates=updates,
            )

            # Start dynamic worker for polling events
            if login_id > 0:
                if device.enabled_access_control_event is True:
                    self.worker_manager.run_device_worker(
                        device_code,
                        WorkerType.DEVICE_EVENTS_POLLING,
                        metadata={"last_uploaded_rec_no": device.last_uploaded_rec_no},
                    )
                    logger.info(
                        "Started worker for device",
                        device_code=device_code,
                        login_id=login_id,
                    )

        except Exception as e:
            logger.error(
                "Error handling device auto register event",
                error=str(e),
                event_data=event.data,
                exc_info=True,
            )
