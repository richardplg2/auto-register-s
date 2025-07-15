import asyncio
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from app.core.containers import Container

from app.workers.base_worker import BaseWorker


class DeviceEventPollingWorker(BaseWorker):
    """Worker for polling events from a specific device"""

    def __init__(self, device_code: str, container: "Container"):
        super().__init__(name=f"device_event_polling_{device_code}")
        self.device_code = device_code
        self.polling_interval = 5

        self.dahua_netsdk_service = container.dahua_netsdk_service()
        self.event_bus = container.event_bus()

        self.logger = structlog.get_logger(__name__, device_code=device_code)

    async def process(self) -> None:
        """Main processing loop - polls events every 5 seconds"""
        self.logger.info("Starting device event polling", device_code=self.device_code)

        while not self.should_stop:
            try:
                await self._poll_device_events()

                # Wait for next poll or stop signal
                await asyncio.sleep(self.polling_interval)

            except asyncio.CancelledError:
                self.logger.info("Polling cancelled", device_code=self.device_code)
                break
            except Exception as e:
                self.logger.error(
                    "Error polling device events",
                    device_code=self.device_code,
                    error=str(e),
                    exc_info=True,
                )
                # Wait a bit before retrying
                await asyncio.sleep(self.polling_interval)

    async def _poll_device_events(self) -> None:
        self.logger.info(
            "Polling events from device",
            device_code=self.device_code,
        )

    async def cleanup(self) -> None:
        """Cleanup when worker stops"""
        self.logger.info(
            "Cleaning up device event polling worker", device_code=self.device_code
        )

        # TODO: Cleanup SDK resources if needed
        # Example:
        # await self.dahua_netsdk_service.logout(self.login_id)
