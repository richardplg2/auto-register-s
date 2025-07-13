import asyncio

from app.core.settings import get_settings
from app.services.dahua_netsdk_service import DahuaNetSDKService
from app.types.dahua_netsdk_types import DeviceAutoRegisterEvent
from app.workers.base_worker import BaseWorker

settings = get_settings()


class AutoRegisterServeWorker(BaseWorker):

    def __init__(self, dahua_netsdk_service: DahuaNetSDKService) -> None:
        super().__init__("auto-register-serve-worker")
        self.dahua_netsdk_service = dahua_netsdk_service
        self.server_handle = None

    async def process(self) -> None:
        self.server_handle = self.dahua_netsdk_service.listen_server(
            settings.AUTO_REGISTER_SERVER_HOST,
            settings.AUTO_REGISTER_SERVER_PORT,
            120000,
            self._discover_device_callback,
        )

        if self.server_handle:
            self.logger.info(
                "Listening for auto registration server...",
                port=settings.AUTO_REGISTER_SERVER_PORT,
                host=settings.AUTO_REGISTER_SERVER_HOST,
            )
        else:
            self.logger.error("Failed to listen for auto registration server.")

        while not self.should_stop:
            await asyncio.sleep(2)

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up...")

    def _discover_device_callback(self, device: DeviceAutoRegisterEvent):
        """Callback for discovered devices"""
        self.logger.info("Discovered device", device_info=device)
        # Handle the discovered device (e.g., register it)
