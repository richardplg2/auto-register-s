import asyncio
from typing import TYPE_CHECKING, Any, Dict, Optional

import aioboto3  # type: ignore
import structlog

if TYPE_CHECKING:
    from app.core.containers import Container

from app.core.settings import get_settings
from app.types.dahua_netsdk_types import AccessCardRecord
from app.workers.base_worker import BaseWorker

settings = get_settings()


class DeviceEventPollingWorker(BaseWorker):
    """
    Worker class responsible for polling events from a specific Dahua device at regular intervals.

    This worker periodically checks for new access card records from the device, processes them,
    and manages event queues for further handling (such as image uploads). It uses asynchronous
    loops to poll device events, process new events, and trigger wakeup intervals for polling.

    Attributes:
        device_code (str): Unique identifier for the device being polled.
        polling_interval (int): Interval in seconds between polling attempts.
        dahua_netsdk_service: Service instance for interacting with Dahua device SDK.
        event_bus: Event bus for publishing or subscribing to events.
        logger: Structured logger for logging events and errors.
        metadata (Optional[Dict[str, Any]]): Additional metadata for worker configuration.
        last_uploaded_rec_no (int): Record number of the last uploaded event.
        polling_wakeup_event (asyncio.Event): Event used to trigger polling cycles.
        new_events_queue (asyncio.Queue[AccessCardRecord]): Queue for newly polled events.

    Methods:
        process(): Main asynchronous loop that starts polling, image upload, and wakeup interval tasks.
        _send_wakeup_interval(): Periodically sets the wakeup event to trigger polling.
        _event_polling_loop(): Waits for wakeup events and polls device for new events.
        _process_new_events(): Processes new events from the queue.
        _poll_device_events(): Polls the device for new access card records and updates the queue.
        cleanup(): Cleans up resources when the worker stops.

    Usage:
        Instantiate with a device code, dependency injection container, and optional metadata.
        Call the `process()` method to start polling events asynchronously.
    """

    """Worker for polling events from a specific device"""

    def __init__(
        self,
        device_code: str,
        container: "Container",
        metadata: Optional[Dict[str, Any]] = {},
    ):
        super().__init__(name=f"device_event_polling_{device_code}")
        self.device_code = device_code
        self.polling_interval = 5

        self.dahua_netsdk_service = container.dahua_netsdk_service()
        self.event_bus = container.event_bus()

        self.logger = structlog.get_logger(__name__, device_code=device_code)
        self.metadata = metadata

        self.last_uploaded_rec_no = metadata.get("last_uploaded_rec_no", -1)  # type: ignore

        self.polling_wakeup_event = asyncio.Event()

        self.new_events_queue: asyncio.Queue[AccessCardRecord] = asyncio.Queue()

        self.aws_session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

    async def process(self) -> None:
        """Main processing loop - polls events every 5 seconds"""
        self.logger.info("Starting device event polling", device_code=self.device_code)

        try:
            await asyncio.gather(
                self._event_polling_loop(),
                self._process_new_events_loop(),
                self._send_wakeup_interval(),
                return_exceptions=True,
            )

        except asyncio.CancelledError:
            self.logger.info("Polling cancelled", device_code=self.device_code)
        except Exception as e:
            self.logger.error(
                "Error polling device events",
                device_code=self.device_code,
                error=str(e),
                exc_info=True,
            )

    async def _send_wakeup_interval(self):
        while not self.should_stop:
            self.polling_wakeup_event.set()
            await asyncio.sleep(self.polling_interval)

    async def _event_polling_loop(self):
        while not self.should_stop:
            try:
                await self.polling_wakeup_event.wait()
                await self._poll_device_events()
                self.polling_wakeup_event.clear()

            except asyncio.CancelledError:
                self.logger.info("Polling cancelled", device_code=self.device_code)
            except Exception as e:
                self.logger.error(
                    "Error polling device events",
                    device_code=self.device_code,
                    error=str(e),
                    exc_info=True,
                )

    async def _process_new_events_loop(self):
        while not self.should_stop:
            try:
                print("Processing new events for device", self.device_code)
                new_access_card_event = await asyncio.wait_for(
                    self.new_events_queue.get(), timeout=10
                )

                await self._process_new_event(new_access_card_event)
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                self.logger.info(
                    "Event processing cancelled", device_code=self.device_code
                )
                break
            except Exception as e:
                self.logger.error(
                    "Error processing events",
                    device_code=self.device_code,
                    error=str(e),
                    exc_info=True,
                )

                await asyncio.sleep(self.polling_interval)

    async def _process_new_event(self, event: AccessCardRecord) -> None:
        self.logger.info(
            "Processing new event",
            device_code=self.device_code,
            rec_no=event.rec_no,
        )

        if event.snap_ftp_url:
            image_data = self.dahua_netsdk_service.download_remote_file(
                self.device_code, event.snap_ftp_url
            )
            if image_data:
                event.image_url = await self._upload_image_to_s3(
                    event.image_name(), image_data
                )

                self.logger.info(
                    "Uploaded image to S3",
                    device_code=self.device_code,
                    image_name=event.image_name(),
                    image_url=event.image_url,
                )

        self.last_uploaded_rec_no = event.rec_no

    async def _upload_image_to_s3(self, file_name: str, data_raw: bytes) -> str | None:
        """Upload image to the s3."""

        async with self.aws_session.client("s3") as s3:  # type: ignore
            bucket_name = settings.AWS_S3_BUCKET
            object_key = f"device_events/{self.device_code}/{file_name}.jpg"

            await s3.put_object(  # type: ignore
                Bucket=bucket_name,
                Key=object_key,
                Body=data_raw,
                ContentType="image/jpeg",
            )

            return f"https://{bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{object_key}"

    async def _poll_device_events(self) -> None:
        self.logger.info(
            "Polling events from device",
            device_code=self.device_code,
            last_uploaded_rec_no=self.last_uploaded_rec_no,
        )

        latest_records = self.dahua_netsdk_service.find_records(
            self.device_code, None, None, None, 1, True
        )

        if len(latest_records) == 0:
            self.logger.info("No latest events found", device_code=self.device_code)
            return

        rec_no_head = latest_records[0].rec_no

        if self.last_uploaded_rec_no == -1:
            self.last_uploaded_rec_no = rec_no_head
            self.logger.info(
                "Initialized last uploaded record number",
                device_code=self.device_code,
                last_uploaded_rec_no=self.last_uploaded_rec_no,
            )
            return

        if rec_no_head < self.last_uploaded_rec_no:
            self.last_uploaded_rec_no = rec_no_head
            return

        records = self.dahua_netsdk_service.find_records_by_rec_no(
            device_code=self.device_code,
            from_rec_no=self.last_uploaded_rec_no + 1,
            n_rec=2000,
            by_asc_order=True,
        )

        if len(records) == 0:
            self.logger.info("No new events found", device_code=self.device_code)
            return

        for record in records:
            if record.rec_no <= self.last_uploaded_rec_no:
                self.logger.warn(
                    "Duplicate event found",
                    device_code=self.device_code,
                    rec_no=record.rec_no,
                )
                continue

            self.logger.info(
                "New event found",
                device_code=self.device_code,
                rec_no=record.rec_no,
            )

            self.new_events_queue.put_nowait(record)

    async def cleanup(self) -> None:
        """Cleanup when worker stops"""
        self.logger.info(
            "Cleaning up device event polling worker", device_code=self.device_code
        )
