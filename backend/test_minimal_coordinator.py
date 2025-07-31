#!/usr/bin/env python3
"""
Minimal coordinator test
"""

print("Creating minimal coordinator...")

class MinimalCoordinator:
    def __init__(self):
        self.running = False
        print("MinimalCoordinator initialized")
    
    def start(self):
        self.running = True
        print("Coordinator started")
    
    def stop(self):
        self.running = False
        print("Coordinator stopped")
    
    def get_status(self):
        return {'running': self.running}

print("Class defined")

# Test instantiation
coordinator = MinimalCoordinator()
coordinator.start()
status = coordinator.get_status()
print(f"Status: {status}")
coordinator.stop()

print("Test completed successfully")