from datetime import datetime
from typing import Any

import structlog
from NetSDK.SDK_Enum import EM_AUTOREGISTER_TYPE  # type: ignore

from app.core.event_bus import Event, EventHandler
from app.core.events import DeviceAutoRegisterEvent
from app.repos.device_repo import DeviceRepo

logger = structlog.get_logger(__name__)


class DeviceAutoRegisterHandler(EventHandler):
    """Handler for device auto register events"""

    def __init__(self, device_repo: DeviceRepo):
        self.device_repo = device_repo

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
                updates = {"is_online": False, "last_disconnected_at": datetime.now()}
            else:
                logger.info("Device is connected", device_code=device_code)
                updates = {
                    "is_online": True,
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

        except Exception as e:
            logger.error(
                "Error handling device auto register event",
                error=str(e),
                event_data=event.data,
                exc_info=True,
            )
