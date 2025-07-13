import ctypes
from ctypes import sizeof
from typing import Any

import structlog
from NetSDK.NetSDK import NetClient  # type: ignore
from NetSDK.SDK_Enum import EM_LOGIN_SPAC_CAP_TYPE  # type: ignore
from NetSDK.SDK_Struct import (  # type: ignore
    NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY,
    NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY,
)

logger = structlog.get_logger(__name__)


class DahuaNetSDKService:
    sdk: NetClient

    def __init__(self) -> None:
        logger.info("Init DahuaNetSDKService")

    async def init(self):
        logger.info("Initializing DahuaNetSDKService...")
        self.sdk = NetClient()
        result = self.sdk.InitEx()  # type: ignore
        if result == 1:
            logger.info("DahuaNetSDKService initialized.")
        else:
            logger.error(
                "Failed to initialize DahuaNetSDKService.",
                msg=self.sdk.GetLastErrorMessage(),
            )

    async def shutdown(self):
        logger.info("DahuaNetSDKService shutting down...")
        self.sdk.Cleanup()
        logger.info("DahuaNetSDKService shut down.")

    def login(
        self, device_ip: str, device_port: int, username: str, password: str
    ):
        """Login to the Dahua device."""
        logger.info("Logging in to Dahua device...")
        stInParam = NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stInParam.dwSize = sizeof(NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY)
        stInParam.szIP = device_ip.encode()
        stInParam.nPort = device_port
        stInParam.szUserName = username.encode()
        stInParam.szPassword = password.encode()

        stInParam.emSpecCap = EM_LOGIN_SPAC_CAP_TYPE.SERVER_CONN

        def get_utf8_string_pointer(src: str):
            b = src.encode("utf-8")
            buf = ctypes.create_string_buffer(len(b) + 1)
            buf.value = b
            return ctypes.cast(buf, ctypes.c_void_p)

        stInParam.pCapParam = get_utf8_string_pointer("test_newfacereg")

        stOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

        # Attempt login
        login_id, device_info, error_msg = self.sdk.LoginWithHighLevelSecurity(  # type: ignore
            stInParam, stOutParam
        )

        print(f"Login ID: {login_id}, Device Info: {device_info}, Error: {error_msg}")

        logger.info("Logged in to Dahua device.")

    def listen_server(
        self,
        host: str,
        port: int,
        timeout: int,
        fn_callback: Any,
    ):
        """Listen for incoming connections on the specified host and port."""

        try:
            result = self.sdk.ListenServer(host, port, timeout, fn_callback, 0)  # type: ignore
            if result > 0:  # type: ignore
                logger.info(
                    "Listening for auto registration server...", port=port, host=host
                )
            else:
                logger.error(
                    "Failed to listen on server.", error=self.sdk.GetLastErrorMessage()
                )

        except Exception as e:
            logger.error("Error occurred while listening on server", error=str(e))
            raise e
