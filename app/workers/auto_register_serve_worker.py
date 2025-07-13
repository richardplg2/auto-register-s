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

    async def process(self) -> None:
        result = self.dahua_netsdk_service.listenServer(
            settings.AUTO_REGISTER_SERVER_HOST,
            settings.AUTO_REGISTER_SERVER_PORT,
            12000,
            self._discover_device_callback,
        )

        while not self.should_stop:
            await asyncio.sleep(2)

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up...")
        await asyncio.sleep(1)

    def _discover_device_callback(self, device: DeviceAutoRegisterEvent):
        """Callback for discovered devices"""
        self.logger.info("Discovered device", device_info=device)
        # Handle the discovered device (e.g., register it)
