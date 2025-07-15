from typing import Any, List, Optional

import structlog
from NetSDK.NetSDK import NetClient  # type: ignore
from NetSDK.SDK_Callback import *  # type: ignore
from NetSDK.SDK_Enum import *  # type: ignore
from NetSDK.SDK_Struct import *  # type: ignore

from app.types.dahua_netsdk_types import AccessCardRecord, UserPayload
from app.utils.dahua_converter import net_time_to_timestamp, timestamp_to_net_time
from app.utils.requests import get_face_image_url_to_bytes

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

        self._setup_log()

    async def shutdown(self):
        logger.info("DahuaNetSDKService shutting down...")
        self.sdk.Cleanup()
        logger.info("DahuaNetSDKService shut down.")

    def _setup_log(self):
        log_info = LOG_SET_PRINT_INFO()
        log_info.dwSize = sizeof(LOG_SET_PRINT_INFO)
        log_info.bSetFilePath = 1
        log_info.szLogFilePath = os.path.join(os.getcwd(), "sdk_log.log").encode("gbk")
        result = self.sdk.LogOpen(log_info)

    def login(
        self,
        device_code: str,
        device_ip: str,
        device_port: int,
        username: str,
        password: str,
    ) -> int:
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
            buf = create_string_buffer(len(b) + 1)
            buf.value = b
            return cast(buf, c_void_p)

        stInParam.pCapParam = get_utf8_string_pointer(device_code)

        stOutParam = NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY()
        stOutParam.dwSize = sizeof(NET_OUT_LOGIN_WITH_HIGHLEVEL_SECURITY)

        # Attempt login
        login_id, _, error_msg = self.sdk.LoginWithHighLevelSecurity(  # type: ignore
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

    def _validate_login(self, device_code: str):
        if not self.sdk:
            raise Exception("SDK is not available.")
        if device_code not in self.sessions:
            raise Exception("Device not logged in")

        if self.sessions[device_code] <= 0:
            raise Exception("Device offline")

    def add_user(
        self,
        device_code: str,
        payload: UserPayload,
    ):
        self._validate_login(device_code)

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
            card_record.szCardName = payload.card_name.encode()
            # Fill basic card information
            card_record.szCardNo = payload.card_no.encode()
            card_record.szUserID = payload.user_id.encode()
            card_record.emStatus = 0  # Card status (0 = normal, 1 = lost, 2 = freeze)
            card_record.emType = 0  # Card type (0 = normal card)
            card_record.szPsw = payload.sz_pw.encode() if payload.sz_pw else b"123456"
            card_record.bIsValid = True  # Card is valid

            # Door permissions
            card_record.nDoorNum = 1  # Number of doors
            card_record.sznDoors[0] = 0  # Door index (first door = 0)

            # Time section permissions
            card_record.nTimeSectionNum = 1  # Number of time sections
            card_record.sznTimeSectionNo[0] = 0  # Time section index

            # User times (for guest cards)
            card_record.nUserTime = 0  # 0 for regular cards, >0 for guest cards

            # Validity period
            card_record.stuValidStartTime = timestamp_to_net_time(
                payload.valid_start_time if payload.valid_start_time else 0
            )

            card_record.stuValidEndTime = timestamp_to_net_time(
                payload.valid_end_time if payload.valid_end_time else 0
            )

            # First enter settings
            card_record.bFirstEnter = payload.first_enter

            # Personal information
            card_record.szCitizenIDNo = (
                payload.citizen_id_no.encode() if payload.citizen_id_no else b""
            )  # ID card number
            card_record.nSpecialDaysScheduleNum = 0  # No special days
            card_record.nUserType = 0  # User type
            card_record.nFloorNum = 0  # No floor restrictions
            card_record.emSex = 0  # Sex (0 = unknown, 1 = male, 2 = female)
            card_record.szRole = b"Employee"  # Role
            card_record.bPersonStatus = True  # Person status
            card_record.emAuthority = 0  # Authority
            card_record.bFloorNoExValid = False
            card_record.nFloorNumEx = 0
            # card_record.szPhoneNumber = b"13800138000"  # Phone number
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
            stInParam.stuCtrlRecordSetInfo.pBuf = cast(pointer(card_record), c_void_p)
            stInParam.stuCtrlRecordSetInfo.nBufLen = sizeof(
                NET_RECORDSET_ACCESS_CTL_CARD
            )

            # Initialize output parameters (device returns)
            stInParam.stuCtrlRecordSetResult.dwSize = sizeof(
                NET_CTRL_RECORDSET_INSERT_OUT
            )
            stInParam.stuCtrlRecordSetResult.nRecNo = 0  # Will be filled by device

            # Call the SDK function to insert record
            result = self.sdk.ControlDevice(
                login_id,
                CtrlType.RECORDSET_INSERT,
                stInParam,  # type: ignore
                5000,  # Timeout in milliseconds
            )

            if result > 0:
                return True

            raise Exception(self.sdk.GetLastErrorMessage())

        except Exception as e:
            print(f"✗ Exception occurred while adding user: {e}")
            import traceback

            traceback.print_exc()

            logger.error("Error occurred while adding user", error=str(e))
            raise e

    def update_user(
        self,
        device_code: str,
        payload: UserPayload,
    ):
        """
        Update user information.
        """
        self._validate_login(device_code)

        login_id = self.sessions[device_code]

        stInParam = NET_IN_ACCESS_CTL_USER_UPDATE()
        stInParam.dwSize = sizeof(NET_IN_ACCESS_CTL_USER_UPDATE)

        # Fill in user information
        stInParam.szUserID = payload.user_id.encode()
        stInParam.szName = payload.name.encode()
        stInParam.szDepartment = payload.department.encode()
        stInParam.szPosition = payload.position.encode()
        stInParam.szPhone = payload.phone.encode()
        stInParam.szEmail = payload.email.encode()

        result = self.sdk.ControlDevice(
            login_id,
            CtrlType.RECORDSET_UPDATE,
            stInParam,
            5000,
        )

        if result > 0:
            return True

        raise Exception(self.sdk.GetLastErrorMessage())

    def add_face(self, device_code: str, user_id: str, face_photo_url: str):
        """Add a face to a user."""
        self._validate_login(device_code)

        login_id = self.sessions[device_code]

        face_data = get_face_image_url_to_bytes(face_photo_url)

        pstInParam = NET_IN_ACCESS_FACE_SERVICE_INSERT()
        pstInParam.dwSize = sizeof(NET_IN_ACCESS_FACE_SERVICE_INSERT)
        pstInParam.nFaceInfoNum = 1  # Number of face records to add

        # Create face info structure
        faceInfo = NET_ACCESS_FACE_INFO()
        faceInfo.szUserID = user_id.encode()  # User ID (must match existing user)

        # Set up face photo data
        faceInfo.nFacePhoto = 1  # Number of face photos (1 photo)
        faceInfo.nInFacePhotoLen[0] = len(face_data)  # Input photo length
        faceInfo.nOutFacePhotoLen[0] = len(face_data)  # Expected output length

        # Allocate buffer for image data and keep reference
        image_buffer = create_string_buffer(face_data, len(face_data))
        faceInfo.pFacePhoto[0] = cast(image_buffer, c_void_p)

        # Create array of face info (even though we only have 1)
        face_info_array = (NET_ACCESS_FACE_INFO * 1)()
        face_info_array[0] = faceInfo

        # Assign face info array to input parameter
        pstInParam.pFaceInfo = cast(face_info_array, POINTER(NET_ACCESS_FACE_INFO))

        # Create output parameter structure
        pstOutParam = NET_OUT_ACCESS_FACE_SERVICE_INSERT()
        pstOutParam.dwSize = sizeof(NET_OUT_ACCESS_FACE_SERVICE_INSERT)
        pstOutParam.nMaxRetNum = 1  # Maximum return number (should match input count)

        # Allocate memory for failure codes (in case of errors)
        fail_codes = (c_int * 1)()
        pstOutParam.pFailCode = cast(fail_codes, POINTER(c_int))

        result = self.sdk.OperateAccessFaceService(  # type: ignore
            login_id,
            EM_A_NET_EM_ACCESS_CTL_FACE_SERVICE.NET_EM_ACCESS_CTL_FACE_SERVICE_INSERT,
            pstInParam,
            pstOutParam,
            5000,  # Timeout in milliseconds
        )

        print("result", result)

        if result <= 0:  # type: ignore
            raise Exception(self.sdk.GetLastErrorMessage())
        return True

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

    def find_card(self, device_code: str, user_id: Optional[str] = None):
        self._validate_login(device_code)
        login_id = self.sessions[device_code]
        find_condition = NET_A_FIND_RECORD_ACCESSCTLCARD_CONDITION()
        find_condition.dwSize = sizeof(NET_A_FIND_RECORD_ACCESSCTLCARD_CONDITION)
        if user_id:
            print("use find condition")
            find_condition.abUserID = 1
            find_condition.szUserID = user_id.encode()
        st_in = NET_IN_FIND_RECORD_PARAM()
        st_in.dwSize = sizeof(NET_IN_FIND_RECORD_PARAM)
        st_in.emType = EM_NET_RECORD_TYPE.ACCESSCTLCARD
        if user_id:
            st_in.pQueryCondition = cast(pointer(find_condition), c_void_p)

        st_out = NET_OUT_FIND_RECORD_PARAM()
        st_out.dwSize = sizeof(NET_OUT_FIND_RECORD_PARAM)

        result = self.sdk.FindRecord(login_id, st_in, st_out)
        print("result", result)
        return st_out.lFindeHandle

    def find_next_card(
        self, finde_handle: Any, find_count: int
    ) -> Optional[List[NET_RECORDSET_ACCESS_CTL_CARD]]:
        try:
            # 1. Tạo mảng struct giống như Java (tương đương với new NET_RECORDSET_ACCESS_CTL_CARD[nFindCount])
            pst_record = (NET_RECORDSET_ACCESS_CTL_CARD * find_count)()

            # 2. Khởi tạo từng element trong mảng và set dwSize
            for i in range(find_count):
                pst_record[i] = NET_RECORDSET_ACCESS_CTL_CARD()
                pst_record[i].dwSize = sizeof(NET_RECORDSET_ACCESS_CTL_CARD)

            # 3. Thiết lập input parameters
            st_in = NET_IN_FIND_NEXT_RECORD_PARAM()
            st_in.dwSize = sizeof(NET_IN_FIND_NEXT_RECORD_PARAM)
            st_in.lFindeHandle = finde_handle
            st_in.nFileCount = find_count

            # 4. Thiết lập output parameters
            st_out = NET_OUT_FIND_NEXT_RECORD_PARAM()
            st_out.nMaxRecordNum = find_count
            # 5. Cấp phát memory cho pRecordList (tương đương với new Memory() trong Java)
            st_out.pRecordList = cast(pst_record, c_void_p)
            st_out.dwSize = sizeof(NET_OUT_FIND_NEXT_RECORD_PARAM)
            # 6. Gọi SDK API
            result = self.sdk.FindNextRecord(st_in, st_out, 5000)

            if not result:
                logger.warning("FindNextRecord failed")
                return None

            record_count = st_out.nRetRecordNum

            if record_count == 0:
                logger.info("No records found")
                return None

            # 7. Extract dữ liệu từ mảng (SDK đã fill dữ liệu vào pst_record)
            # Tương đương với GetPointerDataToStructArr trong Java
            records: List[NET_RECORDSET_ACCESS_CTL_CARD] = []

            # 8. Tạo list chỉ chứa số lượng record thực tế trả về
            # (tương đương với tạo pstRecordEx[stNextOut.nRetRecordNum] trong Java)
            for i in range(record_count):
                print("pst_record[i].", pst_record[i])
                print(
                    "pst_record[i].szCardNo",
                    pst_record[i].szCardNo.decode("utf-8", errors="ignore"),
                )
                records.append(pst_record[i])

            return records

        except Exception as e:
            logger.error("Error occurred while finding next card", error=str(e))
            raise e

    # ***
    def find_next_record(self, finde_handle: Any, find_count: int):
        # 1. Tạo mảng struct
        pst_record = (NET_RECORDSET_ACCESS_CTL_CARDREC * find_count)()

        # 2. Khởi tạo từng element trong mảng và set dwsize
        for i in range(find_count):
            pst_record[i] = NET_RECORDSET_ACCESS_CTL_CARDREC()
            pst_record[i].dwSize = sizeof(NET_RECORDSET_ACCESS_CTL_CARDREC)

        # 3. Thiết lập input
        st_next_in = NET_IN_FIND_NEXT_RECORD_PARAM()
        st_next_in.dwSize = sizeof(NET_IN_FIND_NEXT_RECORD_PARAM)
        st_next_in.lFindeHandle = finde_handle
        st_next_in.nFileCount = find_count

        # 4. Thiết lập output parameters
        st_next_out = NET_OUT_FIND_NEXT_RECORD_PARAM()
        st_next_out.nMaxRecordNum = find_count

        # 5. Cấp phát memory cho pRecordList (tương đương với new Memory() trong Java)
        st_next_out.pRecordList = cast(pst_record, c_void_p)
        st_next_out.dwSize = sizeof(NET_OUT_FIND_NEXT_RECORD_PARAM)

        # 6. Gọi SDK API
        result = self.sdk.FindNextRecord(st_next_in, st_next_out, 5000)
        if not result:
            logger.warning("FindNextRecord failed")
            return None

        record_count = st_next_out.nRetRecordNum
        if record_count == 0:
            logger.info("No records found")
            return None

        return st_next_out

    def find_user(self, device_code: str, user_id: Optional[str] = None):
        self._validate_login(device_code)

        finde_handle = self.find_card(device_code, user_id)

        records = self.find_next_card(finde_handle, 1)

        if not records:
            return None

        return records[0]

    def find_user_v2(
        self, device_code: str, user_id: str
    ) -> NET_OUT_ACCESS_USER_SERVICE_GET:
        self._validate_login(device_code)
        login_id = self.sessions[device_code]
        st_in = NET_IN_ACCESS_USER_SERVICE_GET()
        st_in.dwSize = sizeof(NET_IN_ACCESS_USER_SERVICE_GET)
        st_in.szUserID = user_id.encode()
        st_in.nUserNum = 1

        st_out = NET_OUT_ACCESS_USER_SERVICE_GET()
        st_out.dwSize = sizeof(NET_OUT_ACCESS_USER_SERVICE_GET)
        st_out.nMaxRetNum = 1

        result = self.sdk.OperateAccessUserService(
            login_id,
            EM_A_NET_EM_ACCESS_CTL_USER_SERVICE.NET_EM_ACCESS_CTL_USER_SERVICE_GET,
            st_in,
            st_out,
            5000,
        )

        return st_out

    def list_users(self, device_code: str) -> list[UserPayload]:
        """List users for a specific device."""
        self._validate_login(device_code)

        n_find_count = 50
        try:
            finde_handle = self.find_card(device_code)
            records = self.find_next_card(finde_handle, n_find_count)

            if not records:
                return []

            # Convert NET_RECORDSET_ACCESS_CTL_CARD records to UserPayload objects
            users: List[UserPayload] = []
            for record in records:
                try:
                    user = UserPayload(
                        card_name=record.szCardName.decode(
                            "utf-8", errors="ignore"
                        ).rstrip("\x00"),
                        card_no=record.szCardNo.decode("utf-8", errors="ignore").rstrip(
                            "\x00"
                        ),
                        user_id=record.szUserID.decode("utf-8", errors="ignore").rstrip(
                            "\x00"
                        ),
                        sz_pw=(
                            record.szPsw.decode("utf-8", errors="ignore").rstrip("\x00")
                            if record.szPsw
                            else None
                        ),
                        valid_start_time=(
                            net_time_to_timestamp(record.stuValidStartTime)
                            if hasattr(record, "stuValidStartTime")
                            else None
                        ),
                        valid_end_time=(
                            net_time_to_timestamp(record.stuValidEndTime)
                            if hasattr(record, "stuValidEndTime")
                            else None
                        ),
                        first_enter=bool(record.bFirstEnter),
                        citizen_id_no=(
                            record.szCitizenIDNo.decode(
                                "utf-8", errors="ignore"
                            ).rstrip("\x00")
                            if record.szCitizenIDNo
                            else None
                        ),
                    )
                    users.append(user)
                except Exception as e:
                    logger.warning(f"Failed to parse record: {e}")
                    continue

            return users
        except Exception as e:
            logger.error("Error occurred while listing users", error=str(e))
            raise e

    def get_records_from_pointer(
        self, st_next_out: NET_OUT_FIND_NEXT_RECORD_PARAM
    ) -> List[NET_RECORDSET_ACCESS_CTL_CARDREC]:
        """
        Extract records from C pointer - equivalent to Java's GetPointerDataToStructArr
        """
        records: List[NET_RECORDSET_ACCESS_CTL_CARDREC] = []

        if not st_next_out.pRecordList or st_next_out.nRetRecordNum == 0:
            return records

        # Cast the pointer to the appropriate type
        record_ptr = cast(
            st_next_out.pRecordList, POINTER(NET_RECORDSET_ACCESS_CTL_CARDREC)
        )

        # Extract each record from the pointer array
        for i in range(st_next_out.nRetRecordNum):
            # Get the record at index i
            record = record_ptr[i]
            records.append(record)

        return records

    def find_records(
        self,
        device_code: str,
        card_no: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        n_rec: Optional[int] = 1,
        by_asc_order: Optional[bool] = True,
    ) -> List[AccessCardRecord]:
        self._validate_login(device_code)
        login_id = self.sessions[device_code]
        find_condition = NET_FIND_RECORD_ACCESSCTLCARDREC_CONDITION_EX()
        find_condition.dwSize = sizeof(NET_FIND_RECORD_ACCESSCTLCARDREC_CONDITION_EX)
        if card_no:
            find_condition.bCardNoEnable = 1
            find_condition.szCardNo = card_no.encode()
        else:
            find_condition.bCardNoEnable = 0
        if start_time and end_time:
            find_condition.bTimeEnable = 1
            find_condition.stStartTime = timestamp_to_net_time(start_time)
            find_condition.stEndTime = timestamp_to_net_time(end_time)
        else:
            find_condition.bTimeEnable = 0

        find_order = NET_FIND_RECORD_ACCESSCTLCARDREC_ORDER()
        if by_asc_order:
            find_order.emOrderType = 1
        else:
            find_order.emOrderType = 2
        find_order.emField = 1

        find_condition.nOrderNum = 1
        find_condition.stuOrders[0] = find_order

        st_in = NET_IN_FIND_RECORD_PARAM()
        st_in.dwSize = sizeof(NET_IN_FIND_RECORD_PARAM)
        st_in.emType = EM_NET_RECORD_TYPE.ACCESSCTLCARDREC_EX
        st_in.pQueryCondition = cast(pointer(find_condition), c_void_p)

        st_out = NET_OUT_FIND_RECORD_PARAM()
        st_out.dwSize = sizeof(NET_OUT_FIND_RECORD_PARAM)
        find_record_result = self.sdk.FindRecord(login_id, st_in, st_out, 5000)
        if not find_record_result:
            return []

        ### Find next record
        n_remain_records_to_find = 0
        max_records_find_for_each_request = 2000

        if n_rec and n_rec > 0:
            max_records_find_for_each_request = n_rec if n_rec < 2000 else 2000
            n_remain_records_to_find = n_rec
        else:
            n_remain_records_to_find = 100000

        # List to store all records
        pst_record_ex_list: List[AccessCardRecord] = []

        # Implement do-while loop logic equivalent in Python
        while True:
            st_next_out = self.find_next_record(
                st_out.lFindeHandle, max_records_find_for_each_request
            )

            if st_next_out is None:
                break
            record_count = st_next_out.nRetRecordNum

            record_list = cast(
                st_next_out.pRecordList, POINTER(NET_RECORDSET_ACCESS_CTL_CARDREC)
            )

            for i in range(record_count):
                pst_record_ex_list.append(
                    AccessCardRecord.from_net_recordset(record_list[i])
                )
                n_remain_records_to_find -= 1

                if n_remain_records_to_find == 0:
                    break

            # Continue while we haven't found enough records and there are still records available
            if st_next_out.nRetRecordNum == 0 or n_remain_records_to_find <= 0:
                break

        return pst_record_ex_list

    def find_records_by_rec_no(
        self, device_code: str, from_rec_no: int, n_rec: int, by_asc_order: bool
    ) -> List[AccessCardRecord]:
        """Find records by record number range."""
        self._validate_login(device_code)
        login_id = self.sessions[device_code]

        find_condition = NET_FIND_RECORD_ACCESSCTLCARDREC_CONDITION_EX()
        find_condition.dwSize = sizeof(NET_FIND_RECORD_ACCESSCTLCARDREC_CONDITION_EX)
        find_condition.bCardNoEnable = 0
        find_condition.bTimeEnable = 0

        find_order = NET_FIND_RECORD_ACCESSCTLCARDREC_ORDER()
        if by_asc_order:
            find_order.emOrderType = 1
        else:
            find_order.emOrderType = 2
        find_order.emField = 1

        find_condition.nOrderNum = 1
        find_condition.stuOrders[0] = find_order

        st_in = NET_IN_FIND_RECORD_PARAM()
        st_in.dwSize = sizeof(NET_IN_FIND_RECORD_PARAM)
        st_in.emType = EM_NET_RECORD_TYPE.ACCESSCTLCARDREC_EX
        st_in.pQueryCondition = cast(pointer(find_condition), c_void_p)

        st_out = NET_OUT_FIND_RECORD_PARAM()
        st_out.dwSize = sizeof(NET_OUT_FIND_RECORD_PARAM)

        find_record_result = self.sdk.FindRecord(login_id, st_in, st_out, 5000)
        if not find_record_result:
            return []

        ### Find next record
        n_remain_records_to_find = n_rec
        max_records_find_for_each_request = 2000

        # List to store all records
        pst_record_ex_list: List[AccessCardRecord] = []

        # Implement do-while loop logic equivalent in Python
        while True:

            st_next_out = self.find_next_record(
                st_out.lFindeHandle, max_records_find_for_each_request
            )

            if st_next_out is None:
                break
            record_count = st_next_out.nRetRecordNum

            record_list = cast(
                st_next_out.pRecordList, POINTER(NET_RECORDSET_ACCESS_CTL_CARDREC)
            )

            for i in range(record_count):
                if record_list[i].nRecNo < from_rec_no:
                    continue

                pst_record_ex_list.append(
                    AccessCardRecord.from_net_recordset(record_list[i])
                )
                n_remain_records_to_find -= 1

                if n_remain_records_to_find == 0:
                    break

            # Continue while we haven't found enough records and there are still records available
            if st_next_out.nRetRecordNum == 0 or n_remain_records_to_find <= 0:
                break

        return pst_record_ex_list

    def get_device_info(self, device_code: str):
        self._validate_login(device_code)
        login_id = self.sessions[device_code]
        version_info = NET_A_DEV_VERSION_INFO()
        version_info.dwSize = sizeof(NET_A_DEV_VERSION_INFO)  # Set size field

        # Create variable to receive actual returned length
        ret_len = c_int(0)

        result = self.sdk.QueryDevState(
            login_id,  # Login ID
            EM_QUERY_DEV_STATE_TYPE.SOFTWARE,  # Query type (software version)
            version_info,  # Direct pointer to struct
            sizeof(NET_A_DEV_VERSION_INFO),  # Buffer size
            0,  # Variable to receive actual length (not pointer)
            5000,  # Timeout in milliseconds
        )

        return {
            "szDevSerialNo": version_info.szDevSerialNo.decode(
                "utf-8", errors="ignore"
            ).rstrip("\x00"),
            "szSoftWareVersion": version_info.szSoftWareVersion.decode(
                "utf-8", errors="ignore"
            ).rstrip("\x00"),
            "szPeripheralSoftwareVersion": version_info.szPeripheralSoftwareVersion.decode(
                "utf-8", errors="ignore"
            ).rstrip(
                "\x00"
            ),
        }

    def download_remote_file(self, device_code: str, file_path: str):
        self._validate_login(device_code)
        login_id = self.sessions[device_code]
        st_in = NET_IN_DOWNLOAD_REMOTE_FILE()
        st_in.dwSize = sizeof(NET_IN_DOWNLOAD_REMOTE_FILE)
        st_in.pszFileName = cast(file_path.encode("utf-8"), c_void_p)  # type: ignore
        st_in.pszFileDst = cast(b"", c_void_p)  # type: ignore

        st_out = NET_OUT_DOWNLOAD_REMOTE_FILE()
        st_out.dwMaxFileBufLen = 999999
        file_buf = create_string_buffer(999999)
        st_out.pstFileBuf = cast(file_buf, c_void_p)
        memset(file_buf, 0, 999999)

        result = self.sdk.DownloadRemoteFile(login_id, st_in, st_out, 6000)
        if not result:
            logger.error(
                "Error downloading remote file",
                device_code=device_code,
                file_path=file_path,
                error=self.sdk.GetLastErrorMessage(),
            )
            return None

        return file_buf.raw
