#!/usr/bin/env python3
"""
Simple test to check coordinator import issues
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')
django.setup()

print("Django setup complete")

try:
    print("Testing individual imports...")
    
    # Test dataclass imports
    from dataclasses import dataclass, asdict
    print("✓ dataclass imports OK")
    
    # Test Django imports
    from django.core.cache import cache
    from django.core.mail import send_mail
    from django.db import connections
    from django.conf import settings
    from django.utils import timezone
    print("✓ Django imports OK")
    
    # Test Celery import
    try:
        from celery import current_app
        print("✓ Celery import OK")
    except ImportError as e:
        print(f"⚠ Celery import failed: {e}")
    
    # Test component imports
    try:
        from core.database_maintenance import DatabaseMaintenanceScheduler, run_database_maintenance
        print("✓ database_maintenance import OK")
    except ImportError as e:
        print(f"⚠ database_maintenance import failed: {e}")
    
    try:
        from core.database_monitor import DatabaseMonitor
        print("✓ database_monitor import OK")
    except ImportError as e:
        print(f"⚠ database_monitor import failed: {e}")
    
    try:
        from core.backup_manager import BackupManager
        print("✓ backup_manager import OK")
    except ImportError as e:
        print(f"⚠ backup_manager import failed: {e}")
    
    try:
        from core.performance_monitor import PerformanceMonitor
        print("✓ performance_monitor import OK")
    except ImportError as e:
        print(f"⚠ performance_monitor import failed: {e}")
    
    try:
        from core.database_security import DatabaseSecurityManager
        print("✓ database_security import OK")
    except ImportError as e:
        print(f"⚠ database_security import failed: {e}")
    
    print("\nTesting coordinator import...")
    
    # Now test the coordinator
    import core.ongoing_maintenance_coordinator as omc
    print("✓ Module imported")
    
    # Check what's in the module
    attrs = [x for x in dir(omc) if not x.startswith('_')]
    print(f"Available attributes: {attrs}")
    
    # Try to access the class directly
    if hasattr(omc, 'OngoingMaintenanceCoordinator'):
        print("✓ OngoingMaintenanceCoordinator class found")
        coordinator_class = getattr(omc, 'OngoingMaintenanceCoordinator')
        print(f"Class: {coordinator_class}")
    else:
        print("✗ OngoingMaintenanceCoordinator class not found")
        
        # Check if there are any exceptions during import
        print("Checking for import errors...")
        
        # Try to reload the module to see errors
        import importlib
        try:
            importlib.reload(omc)
            print("Module reloaded successfully")
        except Exception as e:
            print(f"Error during reload: {e}")
            import traceback
            traceback.print_exc()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()