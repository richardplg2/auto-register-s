import datetime
from time import time

from NetSDK.SDK_Struct import NET_TIME  # type: ignore


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
