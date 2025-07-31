"""
Simple test of the performance benchmarker
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

# Test basic imports
print("Testing basic imports...")

try:
    import logging
    import time
    import threading
    import statistics
    import psutil
    import json
    from typing import Dict, Any, List, Optional, Tuple, Callable
    from dataclasses import dataclass, asdict, field
    from datetime import datetime, timedelta
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from contextlib import contextmanager
    print("✓ Basic imports successful")
except Exception as e:
    print(f"✗ Basic imports failed: {e}")
    sys.exit(1)

try:
    from django.db import connections, connection
    from django.db.utils import OperationalError, DatabaseError
    from django.core.management.base import BaseCommand
    from django.conf import settings
    from django.utils import timezone
    from django.test.utils import override_settings
    print("✓ Django imports successful")
except Exception as e:
    print(f"✗ Django imports failed: {e}")
    sys.exit(1)

# Test the problematic imports
try:
    from core.query_optimizer import QueryPerformanceMonitor, monitor_query_performance
    print("✓ Query optimizer imports successful")
except Exception as e:
    print(f"⚠ Query optimizer imports failed: {e}")

try:
    from core.cache_manager import cache_manager
    print("✓ Cache manager imports successful")
except Exception as e:
    print(f"⚠ Cache manager imports failed: {e}")

print("\nAll basic components are working. The issue might be in the performance_benchmarker.py file structure.")