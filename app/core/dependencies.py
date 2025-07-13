"""FastAPI dependency injection utilities."""

from fastapi import Request

from app.core.containers import Container


def get_container(request: Request) -> Container:
    """Get the dependency injection container from the FastAPI app state."""
    return request.app.state.container
