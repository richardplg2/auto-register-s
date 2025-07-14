import datetime

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


def net_time_to_timestamp(net_time: NET_TIME) -> int:
    """
    Convert a NET_TIME object to a Unix timestamp.
    """
    try:
        # Check if the NET_TIME has valid values
        if net_time.dwYear == 0 or net_time.dwMonth == 0 or net_time.dwDay == 0:
            return 0

        dt = datetime.datetime(
            year=net_time.dwYear,
            month=net_time.dwMonth,
            day=net_time.dwDay,
            hour=net_time.dwHour,
            minute=net_time.dwMinute,
            second=net_time.dwSecond,
            tzinfo=datetime.UTC,
        )
        return int(dt.timestamp())
    except (ValueError, AttributeError):
        # Return 0 for invalid dates
        return 0
