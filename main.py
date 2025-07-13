import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.apis import router_v1
from app.core.containers import Container
from app.core.logging import setup_logging
from app.core.settings import get_settings
from app.workers.worker_manager import WorkerManager

settings = get_settings()

logger = logging.getLogger("auto_register")


@asynccontextmanager
async def lifespan(app: FastAPI):
    container: Container = app.state.container
    setup_logging()

    logger.info("Application starting up...")

    # Initialize container resources
    container.init_resources()

    # Manually initialize database
    db = container.db()
    await db.init()

    dh_service = container.dahua_netsdk_service()
    await dh_service.init()

    worker_manager = WorkerManager(container)
    worker_manager.start_all()

    yield

    logger.info("Application shutting down...")
    worker_manager.stop_all()
    await dh_service.shutdown()
    # Shutdown resources
    db = container.db()
    await db.shutdown()
    container.shutdown_resources()
    logger.info("Container resources shutdown complete")


def create_app() -> FastAPI:
    container = Container()

    app = FastAPI(
        title="Auto Register Service API",
        description="Health check and management endpoints for Dahua Camera Auto Registration Service",
        version=settings.SERVICE_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.state.container = container

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router_v1)

    return app


def start():

    uvicorn.run(
        "main:create_app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        workers=1,
        reload=settings.is_development(),
        factory=True,
    )


if __name__ == "__main__":
    start()
