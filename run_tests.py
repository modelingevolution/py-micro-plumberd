#!/usr/bin/env python3
"""Run tests without installing the package."""

import sys
import os
import subprocess

# Add the package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check if required dependencies are available
try:
    import esdbclient
    import pytest
    import pytest_asyncio
except ImportError as e:
    print(f"Error: Missing required dependency - {e}")
    print("\nPlease install the required dependencies:")
    print("pip install esdbclient pytest pytest-asyncio python-dateutil")
    sys.exit(1)

# Run pytest
if __name__ == "__main__":
    sys.exit(pytest.main(["-v", "tests/"]))