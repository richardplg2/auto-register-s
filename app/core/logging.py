"""Logging configuration for Auto Register Service"""

from __future__ import annotations

import logging

import structlog

from app.core.settings import get_settings

settings = get_settings()


def setup_logging():
    """Setup structured logging"""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            # structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # structlog.processors.JSONRenderer(),
            structlog.dev.ConsoleRenderer(),
            structlog.dev.set_exc_info,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )

    logger = structlog.get_logger("auto_register")
    logger.info("Logging configured", service="auto_register")
