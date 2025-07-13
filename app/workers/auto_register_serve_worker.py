import asyncio
import ctypes
import time
from datetime import datetime
from typing import Any

from NetSDK.SDK_Callback import fServiceCallBack  # type: ignore
from NetSDK.SDK_Enum import EM_AUTOREGISTER_TYPE  # type: ignore

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

    async def _discover_device_callback(self, event: DeviceAutoRegisterEvent):
        """Callback for discovered devices"""
        self.logger.info("Discovered device", device_info=event.__dict__)

        # Get device by code
        device = await self.device_repo.get_by_code(event.device_code)
        if device is None or device.is_active is False:
            self.logger.info(
                "Device is not registered or inactive", device_code=event.device_code
            )
            return

        # Update device status based on command
        if event.command == EM_AUTOREGISTER_TYPE.DISCONNECT:
            self.logger.info("Device is disconnected", device_code=event.device_code)
            # Update device as offline
            await self.device_repo.update_device_by_code(
                event.device_code,
                {"is_online": False, "last_disconnected_at": datetime.now()},
            )
        else:
            self.logger.info("Device is connected", device_code=event.device_code)
            # Update device as online and update IP/port if changed
            updates: dict[str, Any] = {
                "is_online": True,
                "last_connected_at": datetime.now(),
                "ip": event.ip,
                "port": event.port,
            }
            await self.device_repo.update_device_by_code(event.device_code, updates)
