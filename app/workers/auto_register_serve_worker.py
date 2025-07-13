import asyncio
import ctypes
import time

from NetSDK.SDK_Callback import fServiceCallBack  # type: ignore

from app.core.containers import Container
from app.core.settings import get_settings
from app.types.dahua_netsdk_types import DeviceAutoRegisterEvent
from app.workers.base_worker import BaseWorker

settings = get_settings()


class AutoRegisterServeWorker(BaseWorker):

    def __init__(self, container: Container) -> None:
        super().__init__("auto-register-serve-worker")
        self.dahua_netsdk_service = container.dahua_netsdk_service()
        self.device_repo = container.device_repo()
        self.server_handle = None

    async def process(self) -> None:

        fn_callback = fServiceCallBack(self.service_callback)  # type: ignore

        self.dahua_netsdk_service.listen_server(
            settings.AUTO_REGISTER_SERVER_HOST,
            settings.AUTO_REGISTER_SERVER_PORT,
            120000,
            fn_callback,
        )

        while not self.should_stop:
            time.sleep(2)

    def service_callback(self, lHandle, pIp, wPort, lCommand, pBuf, dwBufLen, dwUser):  # type: ignore
        """Callback function for service events"""

        self.logger.info(
            "Service event received",
            event_info={
                "Handle": lHandle,
                "IP": pIp.decode(),  # type: ignore
                "Port": wPort,
                "Command": lCommand,
                "Buffer Length": dwBufLen,
                "User": dwUser,
            },
        )

        # Parse device_id from pBuf (similar to Java code)
        device_id = ""
        try:
            if pBuf and dwBufLen > 0:
                buf = ctypes.string_at(pBuf, dwBufLen)  # type: ignore
                device_id = buf.decode("utf-8").strip()
        except Exception as e:
            self.logger.error("Failed to decode device_id", error=str(e))

        event = DeviceAutoRegisterEvent(
            ip=pIp.decode(),  # type: ignore
            port=wPort,  # type: ignore
            command=lCommand,  # type: ignore
            device_code=device_id,
        )

        try:
            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.create_task(self._discover_device_callback(event))

        return 0

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up...")

    async def _discover_device_callback(self, device: DeviceAutoRegisterEvent):
        """Callback for discovered devices"""
        self.logger.info("Discovered device", device_info=device.__dict__)
        # Handle the discovered device (e.g., register it)
