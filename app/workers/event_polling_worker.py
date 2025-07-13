import asyncio

from .base_worker import BaseWorker


class EventPollingWorker(BaseWorker):
    def __init__(self) -> None:
        super().__init__("event-polling-worker")

    async def process(self) -> None:
        while not self.should_stop:
            self.logger.info("Polling for events...", worker=self.name)
            await asyncio.sleep(1)

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up event polling...", worker=self.name)
        await asyncio.sleep(1)
