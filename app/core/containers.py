import asyncio

from dependency_injector import containers, providers

from app.core.database import Database
from app.core.event_bus import AsyncEventBus
from app.core.settings import Settings
from app.handlers.device_event_handler import DeviceAutoRegisterHandler
from app.repos.device_repo import DeviceRepo
from app.services.dahua_netsdk_service import DahuaNetSDKService


class Container(containers.DeclarativeContainer):
    """Dependency injection container for the application."""

    # Configuration
    settings = providers.Singleton(Settings)

    # Database singleton - managed manually in lifespan
    db = providers.Singleton(Database, settings=settings.provided)

    dahua_netsdk_service = providers.Singleton(DahuaNetSDKService)

    # Event Bus - will be initialized with main loop
    event_bus = providers.Singleton(AsyncEventBus)

    # Repositories - will be created lazily after db is initialized
    device_repo = providers.Factory(
        DeviceRepo, session_factory=db.provided.session_factory
    )

    # Event Handlers
    device_auto_register_handler = providers.Factory(
        DeviceAutoRegisterHandler, device_repo=device_repo
    )

    def initialize_container_resources(self):
        """Initialize container resources"""
        # Set the main event loop for event bus
        main_loop = asyncio.get_event_loop()
        self.event_bus().set_main_loop(main_loop)

    def setup_event_handlers(self):
        """Setup event handlers"""
        event_bus = self.event_bus()

        # Register device event handler
        device_handler = self.device_auto_register_handler()
        event_bus.subscribe("device_auto_register", device_handler)

    def shutdown_container_resources(self):
        """Shutdown container resources"""
        # Clean up any resources if needed
        pass
