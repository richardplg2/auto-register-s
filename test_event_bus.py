#!/usr/bin/env python3
"""
Test script để simulate device auto register event
"""
import asyncio
import time

import requests

from app.core.containers import Container
from app.core.events import DeviceAutoRegisterEvent


async def test_event_bus():
    print("Testing Event Bus...")

    # Create container instance
    container = Container()

    # Initialize event bus
    main_loop = asyncio.get_event_loop()
    event_bus = container.event_bus()
    event_bus.set_main_loop(main_loop)

    # Setup handler
    device_handler = container.device_auto_register_handler()
    event_bus.subscribe("device_auto_register", device_handler)

    await event_bus.start()

    print("Event bus initialized successfully!")

    # Create test event
    test_event = DeviceAutoRegisterEvent(
        device_code="TEST_DEVICE_001",
        ip="192.168.1.100",
        port=37777,
        command=1,  # CONNECT
    )

    print(f"Publishing test event: {test_event.device_code}")

    # Publish event
    await event_bus.publish(test_event)

    # Wait for processing
    await asyncio.sleep(1)

    # Get stats
    stats = event_bus.get_stats()
    print(f"Event bus stats after test: {stats}")

    await event_bus.stop()


def test_api_endpoints():
    print("Testing API endpoints...")

    # Test health endpoint
    response = requests.get("http://localhost:8000/v1/healthy/")
    print(f"Health check: {response.json()}")

    # Test event bus stats endpoint
    response = requests.get("http://localhost:8000/v1/healthy/event-bus")
    print(f"Event bus stats: {response.json()}")


if __name__ == "__main__":
    # Test API endpoints first
    test_api_endpoints()

    print("\n" + "=" * 50 + "\n")

    # Test event bus functionality
    asyncio.run(test_event_bus())
