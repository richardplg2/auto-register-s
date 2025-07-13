from dependency_injector import containers, providers

from app.core.database import Database
from app.core.settings import Settings
from app.repos.device_repo import DeviceRepo
from app.services.dahua_netsdk_service import DahuaNetSDKService


class Container(containers.DeclarativeContainer):
    """Dependency injection container for the application."""

    # Configuration
    settings = providers.Singleton(Settings)

    # Database singleton - managed manually in lifespan
    db = providers.Singleton(Database, settings=settings.provided)

    dahua_netsdk_service = providers.Singleton(DahuaNetSDKService)

    # Repositories - will be created lazily after db is initialized
    device_repo = providers.Factory(
        DeviceRepo, session_factory=db.provided.session_factory
    )
