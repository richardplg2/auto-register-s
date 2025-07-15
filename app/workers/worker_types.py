from enum import Enum


class WorkerType(str, Enum):
    MAIN = "main"

    DEVICE_EVENTS_POLLING = "device_events_polling"
