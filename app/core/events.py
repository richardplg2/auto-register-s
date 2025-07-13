from typing import Any

from app.core.event_bus import Event


class DeviceEvent(Event):
    """Device related event"""

    def __init__(self, event_type: str, device_code: str, **kwargs: Any):
        data = {"device_code": device_code, **kwargs}
        super().__init__(event_type=event_type, data=data)


class DeviceAutoRegisterEvent(DeviceEvent):
    """Device auto register event"""

    def __init__(self, device_code: str, ip: str, port: int, command: int):
        super().__init__(
            event_type="device_auto_register",
            device_code=device_code,
            ip=ip,
            port=port,
            command=command,
        )

    @property
    def ip(self) -> str:
        return self.data["ip"]

    @property
    def port(self) -> int:
        return self.data["port"]

    @property
    def command(self) -> int:
        return self.data["command"]

    @property
    def device_code(self) -> str:
        return self.data["device_code"]


class DeviceConnectedEvent(DeviceEvent):
    """Device connected event"""

    def __init__(self, device_code: str, ip: str, port: int):
        super().__init__(
            event_type="device_connected", device_code=device_code, ip=ip, port=port
        )


class DeviceDisconnectedEvent(DeviceEvent):
    """Device disconnected event"""

    def __init__(self, device_code: str):
        super().__init__(event_type="device_disconnected", device_code=device_code)
