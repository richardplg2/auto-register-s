import ctypes
from ctypes import sizeof
from typing import Any

import structlog
from NetSDK.NetSDK import NetClient  # type: ignore
from NetSDK.SDK_Enum import (  # type: ignore
    EM_LOGIN_SPAC_CAP_TYPE,
    EM_NET_RECORD_TYPE,
    CtrlType,
)
from NetSDK.SDK_Struct import (  # type: ignore
    NET_CTRL_RECORDSET_INSERT_IN,
    NET_CTRL_RECORDSET_INSERT_OUT,
    NET_CTRL_RECORDSET_INSERT_PARAM,
    NET_IN_LOGIN_WITH_HIGHLEVEL_SECURITY,
    NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY,
    NET_RECORDSET_ACCESS_CTL_CARD,
)

logger = structlog.get_logger(__name__)


class DahuaNetSDKService:
    sdk: NetClient

    sessions: dict[str, int] = {}

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
        self,
        device_code: str,
        device_ip: str,
        device_port: int,
        username: str,
        password: str,
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

        stInParam.pCapParam = get_utf8_string_pointer(device_code)

        stOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

        # Attempt login
        login_id, device_info, error_msg = self.sdk.LoginWithHighLevelSecurity(  # type: ignore
            stInParam, stOutParam
        )

        if login_id > 0:
            logger.info(
                "Logged in to Dahua device.", login_id=login_id, device_code=device_code
            )
            self.sessions[device_code] = login_id
            return login_id
        else:
            logger.error("Failed to login to Dahua device.", error=error_msg)
            raise Exception(error_msg)

    def add_user_demo(self, device_code: str):
        if device_code not in self.sessions:
            logger.error("Device not logged in.", device_code=device_code)
            return
        login_id = self.sessions[device_code]
        try:
            # Create main parameter structure
            stInParam = NET_CTRL_RECORDSET_INSERT_PARAM()
            stInParam.dwSize = sizeof(NET_CTRL_RECORDSET_INSERT_PARAM)

            # Fill input parameters (user writes)
            stInParam.stuCtrlRecordSetInfo.dwSize = sizeof(NET_CTRL_RECORDSET_INSERT_IN)
            stInParam.stuCtrlRecordSetInfo.emType = EM_NET_RECORD_TYPE.ACCESSCTLCARD

            # Create access control card record
            card_record = NET_RECORDSET_ACCESS_CTL_CARD()
            card_record.dwSize = sizeof(NET_RECORDSET_ACCESS_CTL_CARD)

            # Fill basic card information
            card_record.szCardNo = b"CARD002"  # Card number
            card_record.szUserID = b"USER002"  # User ID
            card_record.emStatus = 0  # Card status (0 = normal, 1 = lost, 2 = freeze)
            card_record.emType = 0  # Card type (0 = normal card)
            card_record.szPsw = b"123456"  # Password
            card_record.bIsValid = True  # Card is valid
            card_record.szCardName = b"Test Card"  # Card name

            # Door permissions
            card_record.nDoorNum = 1  # Number of doors
            card_record.sznDoors[0] = 0  # Door index (first door = 0)

            # Time section permissions
            card_record.nTimeSectionNum = 1  # Number of time sections
            card_record.sznTimeSectionNo[0] = 0  # Time section index

            # User times (for guest cards)
            card_record.nUserTime = 0  # 0 for regular cards, >0 for guest cards

            # Validity period
            card_record.stuValidStartTime.dwYear = 2025
            card_record.stuValidStartTime.dwMonth = 7
            card_record.stuValidStartTime.dwDay = 9
            card_record.stuValidStartTime.dwHour = 0
            card_record.stuValidStartTime.dwMinute = 0
            card_record.stuValidStartTime.dwSecond = 0

            card_record.stuValidEndTime.dwYear = 2026
            card_record.stuValidEndTime.dwMonth = 7
            card_record.stuValidEndTime.dwDay = 9
            card_record.stuValidEndTime.dwHour = 23
            card_record.stuValidEndTime.dwMinute = 59
            card_record.stuValidEndTime.dwSecond = 59

            # First enter settings
            card_record.bFirstEnter = False

            # Personal information
            card_record.szCitizenIDNo = b"123456789012345678"  # ID card number
            card_record.nSpecialDaysScheduleNum = 0  # No special days
            card_record.nUserType = 0  # User type
            card_record.nFloorNum = 0  # No floor restrictions
            card_record.emSex = 0  # Sex (0 = unknown, 1 = male, 2 = female)
            card_record.szRole = b"Employee"  # Role
            card_record.bPersonStatus = True  # Person status
            card_record.emAuthority = 0  # Authority
            card_record.bFloorNoExValid = False
            card_record.nFloorNumEx = 0
            card_record.szPhoneNumber = b"13800138000"  # Phone number
            card_record.bFloorNoEx2Valid = False
            card_record.szDefaultFloor = b"1"  # Default floor
            card_record.nUserTimeSectionNum = 0
            card_record.szWorkClass = b"Day Shift"  # Work class
            card_record.nAuthOverdueTime = 0
            card_record.emGreenCNHealthStatus = 0
            card_record.emAllowPermitFlag = 0
            card_record.emRentState = 0
            card_record.nConsumptionTimeSectionsNum = 0
            card_record.nMultiTimeSectionsNum = 0

            # Set buffer pointer and length
            stInParam.stuCtrlRecordSetInfo.pBuf = ctypes.cast(
                ctypes.pointer(card_record), ctypes.c_void_p
            )
            stInParam.stuCtrlRecordSetInfo.nBufLen = sizeof(
                NET_RECORDSET_ACCESS_CTL_CARD
            )

            # Initialize output parameters (device returns)
            stInParam.stuCtrlRecordSetResult.dwSize = sizeof(
                NET_CTRL_RECORDSET_INSERT_OUT
            )
            stInParam.stuCtrlRecordSetResult.nRecNo = 0  # Will be filled by device

            print("Adding access control card with the following information:")
            print(
                f"  Card Number: {card_record.szCardNo.decode('utf-8', errors='ignore')}"
            )
            print(f"  User ID: {card_record.szUserID.decode('utf-8', errors='ignore')}")
            print(
                f"  Card Name: {card_record.szCardName.decode('utf-8', errors='ignore')}"
            )
            print(
                f"  Phone: {card_record.szPhoneNumber.decode('utf-8', errors='ignore')}"
            )
            print(f"  Door Access: {card_record.nDoorNum} door(s)")
            print(
                f"  Valid From: {card_record.stuValidStartTime.dwYear}-{card_record.stuValidStartTime.dwMonth:02d}-{card_record.stuValidStartTime.dwDay:02d}"
            )
            print(
                f"  Valid Until: {card_record.stuValidEndTime.dwYear}-{card_record.stuValidEndTime.dwMonth:02d}-{card_record.stuValidEndTime.dwDay:02d}"
            )

            # Call the SDK function to insert record
            result = self.sdk.ControlDevice(
                login_id,
                CtrlType.RECORDSET_INSERT,
                stInParam,
                5000,  # Timeout in milliseconds
            )

            if result:
                print("✓ Access control card added successfully")
                print(
                    f"  Assigned Record Number: {stInParam.stuCtrlRecordSetResult.nRecNo}"
                )
            else:
                print("✗ Failed to add access control card")

        except Exception as e:
            print(f"✗ Exception occurred while adding user: {e}")
            import traceback

            traceback.print_exc()

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
