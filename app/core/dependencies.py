"""FastAPI dependency injection utilities."""

from fastapi import Request

from app.core.containers import Container
from app.repos.device_repo import DeviceRepo


def get_container(request: Request) -> Container:
    """Get the dependency injection container from the FastAPI app state."""
    return request.app.state.container


def get_device_repo(request: Request) -> DeviceRepo:
    """Get the device repository from the dependency injection container."""
    return get_container(request).device_repo
