#!/usr/bin/env python3
"""
Auto Register Service Launcher
Simple launcher script for the Dahua Auto Register Service
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the service
from auto_register_service.main import run_service

if __name__ == "__main__":
    print("🚀 Starting Dahua Auto Register Service...")
    run_service()
