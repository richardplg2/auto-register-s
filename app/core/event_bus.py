import asyncio
import queue
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Event:
    """Base event class"""

    event_type: str
    data: Dict[str, Any]
    timestamp: float
    source_thread: str

    def __init__(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        self.event_type = event_type
        self.data = data or {}
        self.timestamp = time.time()
        self.source_thread = threading.current_thread().name


class EventHandler(ABC):
    """Abstract event handler"""

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle the event"""
        pass


class AsyncEventBus:
    """Thread-safe event bus that routes events to main event loop"""

    def __init__(
        self,
        main_loop: Optional[asyncio.AbstractEventLoop] = None,
        max_queue_size: int = 1000,
    ):
        self._main_loop = main_loop
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_queue: queue.Queue[Event] = queue.Queue(maxsize=max_queue_size)
        self._running = False
        self._max_queue_size = max_queue_size

        # Statistics
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "queue_peak_size": 0,
        }

    def set_main_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the main event loop"""
        self._main_loop = loop
        logger.info("Event bus main loop set")

    def subscribe(self, event_type: str, handler: EventHandler):
        """Subscribe to event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(
            "Handler subscribed",
            event_type=event_type,
            handler=handler.__class__.__name__,
        )

    def unsubscribe(self, event_type: str, handler: EventHandler):
        """Unsubscribe from event type"""
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                logger.info(
                    "Handler unsubscribed",
                    event_type=event_type,
                    handler=handler.__class__.__name__,
                )

    def publish_threadsafe(self, event: Event):
        """Publish event from any thread - thread safe"""
        if not self._main_loop or self._main_loop.is_closed():
            logger.warning(
                "Main loop not available, dropping event",
                event_type=event.event_type,
                source_thread=threading.current_thread().name,
            )
            return

        event.source_thread = threading.current_thread().name

        try:
            # Put event in queue and schedule processing in main loop
            self._event_queue.put(event, timeout=1.0)  # Add timeout to prevent blocking

            # Schedule processing in main event loop
            self._main_loop.call_soon_threadsafe(self._process_queue)

            # Update statistics
            self._stats["events_published"] += 1
            self._stats["queue_peak_size"] = max(
                self._stats["queue_peak_size"], self._event_queue.qsize()
            )

            logger.debug(
                "Event scheduled for processing",
                event_type=event.event_type,
                source_thread=event.source_thread,
            )

        except queue.Full:
            logger.error(
                "Event queue is full, dropping event",
                event_type=event.event_type,
                source_thread=event.source_thread,
            )
        except RuntimeError as e:
            logger.error(
                "Failed to schedule event processing",
                error=str(e),
                event_type=event.event_type,
                source_thread=event.source_thread,
            )

    async def publish(self, event: Event):
        """Publish event from main thread - async"""
        event.source_thread = threading.current_thread().name
        await self._handle_event(event)

    def _process_queue(self):
        """Process events from queue - runs in main loop"""
        processed_count = 0
        while (
            not self._event_queue.empty() and processed_count < 100
        ):  # Prevent blocking
            try:
                event = self._event_queue.get_nowait()
                # Create task to handle event
                if self._main_loop and not self._main_loop.is_closed():
                    task = self._main_loop.create_task(self._handle_event(event))
                    # Optional: Store task reference to avoid gc
                    task.add_done_callback(lambda t: self._log_task_result(t))
                processed_count += 1
            except queue.Empty:
                break
            except Exception as e:
                logger.error("Error processing event queue", error=str(e))
                break

        if processed_count > 0:
            logger.debug("Processed events from queue", count=processed_count)
            # Update statistics
            self._stats["events_processed"] += processed_count

    def _log_task_result(self, task: asyncio.Task[Any]):
        """Log task completion"""
        try:
            if task.exception():
                logger.error("Event handler task failed", error=str(task.exception()))
                # Update statistics
                self._stats["events_failed"] += 1
        except Exception:
            pass  # Task might be cancelled

    async def _handle_event(self, event: Event):
        """Handle event in main loop"""
        handlers = self._handlers.get(event.event_type, [])

        if not handlers:
            logger.debug("No handlers for event", event_type=event.event_type)
            return

        logger.debug(
            "Processing event",
            event_type=event.event_type,
            handlers_count=len(handlers),
        )

        # Execute all handlers concurrently
        tasks: List[asyncio.Task[Any]] = []
        for handler in handlers:
            try:
                task = asyncio.create_task(handler.handle(event))
                tasks.append(task)
            except Exception as e:
                logger.error(
                    "Failed to create handler task",
                    error=str(e),
                    handler=handler.__class__.__name__,
                )

        # Wait for all handlers to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Update statistics and log any exceptions
            failed_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_count += 1
                    handler_name = (
                        handlers[i].__class__.__name__
                        if i < len(handlers)
                        else "unknown"
                    )
                    logger.error(
                        "Event handler failed",
                        error=str(result),
                        handler=handler_name,
                        event_type=event.event_type,
                    )

            # Update stats
            self._stats["events_processed"] += 1
            if failed_count > 0:
                self._stats["events_failed"] += 1

    async def start(self):
        """Start event bus"""
        self._running = True
        logger.info("Event bus started")

    async def stop(self):
        """Stop event bus"""
        self._running = False

        # Process remaining events
        self._process_queue()

        logger.info("Event bus stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        current_queue_size = self._event_queue.qsize()
        self._stats["queue_peak_size"] = max(
            self._stats["queue_peak_size"], current_queue_size
        )

        return {
            **self._stats,
            "current_queue_size": current_queue_size,
            "max_queue_size": self._max_queue_size,
            "handlers_count": sum(
                len(handlers) for handlers in self._handlers.values()
            ),
            "event_types": list(self._handlers.keys()),
        }

    def reset_stats(self):
        """Reset statistics"""
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "queue_peak_size": 0,
        }
