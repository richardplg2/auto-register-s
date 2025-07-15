import ctypes
import time
from typing import TYPE_CHECKING

from NetSDK.SDK_Callback import fServiceCallBack  # type: ignore
from NetSDK.SDK_Enum import EM_AUTOREGISTER_TYPE  # type: ignore

from app.core.events import DeviceAutoRegisterEvent
from app.core.settings import get_settings
from app.workers.base_worker import BaseWorker

if TYPE_CHECKING:
    from app.core.containers import Container

settings = get_settings()


class AutoRegisterServeWorker(BaseWorker):

    def __init__(self, container: "Container") -> None:
        super().__init__("auto-register-serve-worker")
        self.dahua_netsdk_service = container.dahua_netsdk_service()
        self.event_bus = container.event_bus()
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
            device_code=device_id,
            ip=pIp.decode(),  # type: ignore
            port=wPort,  # type: ignore
            command=lCommand,  # type: ignore
        )

        # Publish event via event bus (thread-safe)
        self.event_bus.publish_threadsafe(event)

        return 0

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up...")
