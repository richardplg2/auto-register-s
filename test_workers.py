#!/usr/bin/env python3
"""Test script to validate worker pattern"""

import asyncio
import time
from app.core.containers import Container
from app.workers.worker_manager import WorkerManager


def test_workers():
    print("🚀 Testing Worker Pattern...")

    # Create container
    container = Container()

    # Create worker manager
    manager = WorkerManager(container)

    print(f"📋 Created {len(manager.workers)} workers")

    # Start workers
    print("▶️  Starting workers...")
    manager.start_all()

    # Let them run for a bit
    print("⏱️  Letting workers run for 5 seconds...")
    time.sleep(5)

    # Stop workers
    print("⏹️  Stopping workers...")
    manager.stop_all()

    print("✅ Test completed successfully!")


if __name__ == "__main__":
    test_workers()
