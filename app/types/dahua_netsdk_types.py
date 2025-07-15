from datetime import datetime
from typing import Any, Optional

from NetSDK.SDK_Enum import EM_AUTOREGISTER_TYPE  # type: ignore
from NetSDK.SDK_Struct import NET_RECORDSET_ACCESS_CTL_CARDREC  # type: ignore

from app.utils.dahua_converter import net_time_to_datetime  # type: ignore


class DeviceAutoRegisterEvent:
    def __init__(
        self, device_code: str, command: EM_AUTOREGISTER_TYPE, ip: str, port: int
    ):
        self.device_code = device_code
        self.command = command
        self.ip = ip
        self.port = port


class UserPayload:
    def __init__(
        self,
        user_id: str,
        card_name: str,
        card_no: str,
        citizen_id_no: Optional[str] = None,
        sz_pw: Optional[str] = None,
        valid_start_time: Optional[int] = None,
        valid_end_time: Optional[int] = None,
        user_name: Optional[str] = None,
        password: Optional[str] = None,
        first_enter: bool = False,
    ):
        self.user_id = user_id
        self.card_name = card_name
        self.card_no = card_no
        self.sz_pw = sz_pw
        self.valid_start_time = valid_start_time
        self.valid_end_time = valid_end_time
        self.user_name = user_name
        self.password = password
        self.first_enter = first_enter
        self.citizen_id_no = citizen_id_no


class AccessCardRecord:
    def __init__(
        self,
        card_no: str,
        rec_no: int,
        card_name: str,
        card_type: int,
        user_id: str,
        reader_id: str,
        door: int,
        b_status: int,
        error_code: int,
        stu_time: datetime,
        method: int,
        snap_ftp_url: str,
        em_direction: int,
        is_over_temparature: bool,
        temperature_unit: int,
        current_temperature: float,
        em_mask: int,
        image_url: Optional[str] = None,
    ):
        self.card_no = card_no
        self.rec_no = rec_no
        self.card_name = card_name
        self.card_type = card_type
        self.user_id = user_id
        self.reader_id = reader_id
        self.door = door
        self.b_status = b_status
        self.error_code = error_code
        self.stu_time = stu_time
        self.method = method
        self.snap_ftp_url = snap_ftp_url
        self.em_direction = em_direction
        self.is_over_temparature = is_over_temparature
        self.temperature_unit = temperature_unit
        self.current_temperature = current_temperature
        self.em_mask = em_mask
        self.image_url = image_url

    def to_webhook_payload(self) -> dict[str, Any]:
        return {
            "CardName": self.card_name,
            "CreateTime": "",
            "CurrentTemperature": self.current_temperature,
            "ErrorCode": self.error_code,
            "IsOverTemperature": self.is_over_temparature,
            "Mask": self.em_mask,
            "Method": self.method,
            "RecNo": self.rec_no,
            "Status": self.b_status,
            "TemperatureUnit": self.temperature_unit,
            "ImageURL": self.image_url,
            "UserID": self.user_id,
        }

    def image_name(self):
        return f"{self.card_no}_{self.rec_no}.jpg"

    @staticmethod
    def from_net_recordset(
        record: NET_RECORDSET_ACCESS_CTL_CARDREC,
    ) -> "AccessCardRecord":
        """
        Initialize AccessCardRecord from NET_RECORDSET_ACCESS_CTL_CARDREC object.
        Assumes `record` has attributes matching the expected fields.
        """
        return AccessCardRecord(
            card_no=getattr(record, "szCardNo", ""),
            rec_no=getattr(record, "nRecNo", 0),
            card_name=getattr(record, "szCardName", ""),
            card_type=record.emCardType,
            user_id=getattr(record, "szUserID", ""),
            reader_id=getattr(record, "szReaderID", ""),
            door=getattr(record, "nDoor", 0),
            b_status=getattr(record, "bStatus", 0),
            error_code=getattr(record, "nErrorCode", 0),
            stu_time=net_time_to_datetime(record.stuTime),
            method=getattr(record, "nMethod", 0),
            snap_ftp_url=getattr(record, "szSnapFtpUrl", ""),
            em_direction=getattr(record, "emDirection", 0),
            is_over_temparature=bool(getattr(record, "bIsOverTemparature", False)),
            temperature_unit=getattr(record, "emTemperatureUnit", 0),
            current_temperature=getattr(record, "fCurrentTemperature", 0.0),
            em_mask=getattr(record, "emMask", 0),
        )
