import asyncio
import threading
from abc import ABC, abstractmethod
from typing import Optional

import structlog


class BaseWorker(
    threading.Thread,
    ABC,
):

    def __init__(self, name: str, daemon: bool = True) -> None:
        super().__init__(daemon=daemon, name=name)
        self.name = name
        self.logger = structlog.get_logger(self.name)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._stop_event = threading.Event()

    @abstractmethod
    async def process(self) -> None:
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        pass

    def run(self) -> None:
        """Thread entry point - runs in separate thread"""
        try:
            # Create new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            self.logger.info("Starting processing", worker=self.name)
            self._loop.run_until_complete(self.process())

        except (asyncio.CancelledError, KeyboardInterrupt):
            self.logger.info("Worker interrupted")
        except RuntimeError as e:
            if "Event loop stopped" in str(e):
                self.logger.info("Worker stopped gracefully")
            else:
                self.logger.error("Runtime error occurred", exc_info=e)
        except Exception as e:
            self.logger.error("Error occurred while processing", exc_info=e)
        finally:
            self.logger.info("Stopping processing")
            self.logger.info("Cleaning up processing")

            # Run cleanup in same loop
            if self._loop and not self._loop.is_closed():
                try:
                    self._loop.run_until_complete(self.cleanup())
                except Exception as e:
                    self.logger.error("Error during cleanup", exc_info=e)
                finally:
                    self._loop.close()

            self.logger.info("Stopped")

    def stop(self, timeout: Optional[float] = 30) -> None:
        """Stop the worker gracefully"""
        self._stop_event.set()

        # Signal the event loop to stop if it exists and is running
        if self._loop and not self._loop.is_closed():
            # Cancel all tasks to allow graceful shutdown
            if not self._loop.is_running():
                return

            # Schedule shutdown in the loop
            try:
                self._loop.call_soon_threadsafe(self._schedule_shutdown)
            except RuntimeError:
                # Loop might already be stopping
                pass

        # Wait for thread to finish
        self.join(timeout)

        if self.is_alive():
            self.logger.warning("Worker did not stop gracefully", worker=self.name)

    def _schedule_shutdown(self):
        """Schedule shutdown tasks in the event loop"""
        if not self._loop:
            return

        # Cancel all running tasks
        tasks = [task for task in asyncio.all_tasks(self._loop) if not task.done()]
        for task in tasks:
            task.cancel()

        # Stop the loop
        self._loop.stop()

    @property
    def should_stop(self) -> bool:
        return self._stop_event.is_set()
