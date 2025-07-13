import structlog
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings import Settings
from app.models.base import BaseModel

logger = structlog.get_logger(__name__)


class Database:
    def __init__(self, settings: Settings):
        self._db_url = settings.get_db_url()
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    async def init(
        self,
    ):
        """Initialize the database connection."""
        logger.info("Initializing database connection", db_url=self._db_url)
        self.engine = create_async_engine(
            self._db_url, pool_pre_ping=True, pool_size=10, max_overflow=20
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        await self.create_all_tables()
        logger.info("Database connection initialized successfully")

    async def create_all_tables(self):
        if self.engine == None:
            return
        async with self.engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)

    async def shutdown(self):
        """Shutdown the database connection."""
        if self.engine:
            logger.info("Database resource: Shutting down...")
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None
            logger.info("Database resource: Shutdown complete.")
