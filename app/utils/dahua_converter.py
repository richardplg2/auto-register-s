import datetime
from time import time

from NetSDK.SDK_Struct import NET_TIME  # type: ignore


def net_time_to_timestamp(net_time: NET_TIME) -> int:
    """
    Convert a NET_TIME object to a Unix timestamp.
    """
    try:
        dt = datetime.datetime(
            year=net_time.dwYear,
            month=net_time.dwMonth,
            day=net_time.dwDay,
            hour=net_time.dwHour,
            minute=net_time.dwMinute,
            second=net_time.dwSecond,
            tzinfo=datetime.timezone.utc,
        )
        return int(dt.timestamp())
    except (ValueError, AttributeError):
        # Return current timestamp if conversion fails
        return int(time())


def timestamp_to_net_time(timestamp: int):
    """
    Convert a Unix timestamp to a NET_TIME object.
    """
    dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC)

    dtc = NET_TIME()
    dtc.dwYear = dt.year
    dtc.dwMonth = dt.month
    dtc.dwDay = dt.day
    dtc.dwHour = dt.hour
    dtc.dwMinute = dt.minute
    dtc.dwSecond = dt.second
    return dtc
