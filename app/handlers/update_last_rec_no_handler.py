import structlog

from app.core.event_bus import Event, EventHandler
from app.repos.device_repo import DeviceRepo

logger = structlog.get_logger(__name__)


class UpdateLastRecNoHandler(EventHandler):
    """Handler for updating the last record number events"""

    def __init__(
        self,
        device_repo: DeviceRepo,
    ):
        self.device_repo = device_repo

    async def handle(self, event: Event) -> None:
        """Handle device auto register event"""
        if event.event_type != "update_last_rec_no":
            return

        try:
            device_code = event.data["device_code"]
            last_rec_no = event.data["last_rec_no"]
            if last_rec_no is None:
                return
            await self.device_repo.update_device_by_code(
                device_code, {"last_uploaded_rec_no": last_rec_no}
            )
        except Exception as e:
            logger.error(
                "Error handling device auto register event",
                error=str(e),
                event_data=event.data,
                exc_info=True,
            )
