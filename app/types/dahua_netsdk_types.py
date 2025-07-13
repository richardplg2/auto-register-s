from NetSDK.SDK_Enum import EM_AUTOREGISTER_TYPE  # type: ignore


class DeviceAutoRegisterEvent:
    def __init__(
        self, device_code: str, command: EM_AUTOREGISTER_TYPE, ip: str, port: int
    ):
        self.device_code = device_code
        self.command = command
        self.ip = ip
        self.port = port
