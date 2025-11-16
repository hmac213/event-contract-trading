#!/usr/bin/env python3
"""
Startup Coordinator for Event Contract Trading System

Manages the startup sequence to ensure:
1. Initial bulk data load completes before polling
2. Services start in correct order
3. Coordination signals between services
"""

import time
import os
from cache.RedisManager import RedisManager
from typing import Optional

class StartupCoordinator:
    """Coordinates startup sequence across services"""
    
    def __init__(self):
        self.redis_manager = RedisManager()
        self.coordination_key_prefix = "startup_coordination"
        
    def set_startup_phase(self, service_name: str, phase: str) -> None:
        """Set the current startup phase for a service"""
        key = f"{self.coordination_key_prefix}:{service_name}:phase"
        self.redis_manager.redis_client.set(key, phase, ex=3600)  # Expire in 1 hour
        print(f"🔄 {service_name}: Phase set to '{phase}'")
    
    def get_startup_phase(self, service_name: str) -> Optional[str]:
        """Get the current startup phase for a service"""
        key = f"{self.coordination_key_prefix}:{service_name}:phase"
        phase = self.redis_manager.redis_client.get(key)
        if phase is None:
            return None
        return phase.decode('utf-8') if isinstance(phase, bytes) else phase
    
    def set_initial_load_complete(self, service_name: str, markets_loaded: int) -> None:
        """Mark initial data load as complete"""
        key = f"{self.coordination_key_prefix}:{service_name}:initial_load_complete"
        metadata = f"{markets_loaded}:{int(time.time())}"
        self.redis_manager.redis_client.set(key, metadata, ex=3600)
        print(f"✅ {service_name}: Initial load complete - {markets_loaded} markets loaded")
    
    def is_initial_load_complete(self, service_name: str) -> bool:
        """Check if initial data load is complete for a service"""
        key = f"{self.coordination_key_prefix}:{service_name}:initial_load_complete"
        return self.redis_manager.redis_client.exists(key) > 0
    
    def get_initial_load_info(self, service_name: str) -> Optional[dict]:
        """Get information about initial load completion"""
        key = f"{self.coordination_key_prefix}:{service_name}:initial_load_complete"
        data = self.redis_manager.redis_client.get(key)
        if not data:
            return None
        
        data_str = data.decode('utf-8') if isinstance(data, bytes) else data
        markets_loaded, timestamp = data_str.split(':')
        return {
            'markets_loaded': int(markets_loaded),
            'completed_at': int(timestamp)
        }
    
    def wait_for_initial_load(self, service_name: str, timeout: int = 300) -> bool:
        """Wait for initial data load to complete"""
        print(f"⏳ Waiting for {service_name} initial data load to complete...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_initial_load_complete(service_name):
                info = self.get_initial_load_info(service_name)
                if info:
                    print(f"✅ {service_name} initial load complete: {info['markets_loaded']} markets")
                return True
            
            time.sleep(2)
        
        print(f"⚠️ Timeout waiting for {service_name} initial load")
        return False
    
    def signal_service_ready(self, service_name: str) -> None:
        """Signal that a service is fully ready"""
        key = f"{self.coordination_key_prefix}:{service_name}:ready"
        self.redis_manager.redis_client.set(key, int(time.time()), ex=3600)
        print(f"🚀 {service_name}: Service ready")
    
    def wait_for_service_ready(self, service_name: str, timeout: int = 300) -> bool:
        """Wait for a service to be ready"""
        print(f"⏳ Waiting for {service_name} to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            key = f"{self.coordination_key_prefix}:{service_name}:ready"
            if self.redis_manager.redis_client.exists(key):
                print(f"✅ {service_name} is ready")
                return True
            time.sleep(2)
        
        print(f"⚠️ Timeout waiting for {service_name} to be ready")
        return False
    
    def cleanup_coordination_data(self) -> None:
        """Clean up all coordination data"""
        pattern = f"{self.coordination_key_prefix}:*"
        keys = self.redis_manager.redis_client.keys(pattern)
        if keys:
            self.redis_manager.redis_client.delete(*keys)
            print(f"🧹 Cleaned up {len(keys)} coordination keys")
    
    def get_startup_status(self) -> dict:
        """Get comprehensive startup status"""
        pattern = f"{self.coordination_key_prefix}:*"
        keys = self.redis_manager.redis_client.keys(pattern)
        
        status = {
            'services': {},
            'last_updated': int(time.time())
        }
        
        for key in keys:
            key_str = key.decode('utf-8')
            parts = key_str.split(':')
            if len(parts) >= 3:
                service_name = parts[2]
                attribute = parts[3] if len(parts) > 3 else 'unknown'
                
                if service_name not in status['services']:
                    status['services'][service_name] = {}
                
                value = self.redis_manager.redis_client.get(key)
                if value:
                    status['services'][service_name][attribute] = value.decode('utf-8')
        
        return status

if __name__ == '__main__':
    # CLI interface for monitoring startup coordination
    import sys
    import json
    
    coordinator = StartupCoordinator()
    
    if len(sys.argv) < 2:
        print("Usage: python startup_coordinator.py <command> [args]")
        print("Commands:")
        print("  status                    - Show startup status")
        print("  wait <service_name>       - Wait for service to be ready")
        print("  cleanup                   - Clean coordination data")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'status':
        status = coordinator.get_startup_status()
        print(json.dumps(status, indent=2))
    
    elif command == 'wait':
        if len(sys.argv) < 3:
            print("Usage: python startup_coordinator.py wait <service_name>")
            sys.exit(1)
        
        service_name = sys.argv[2]
        success = coordinator.wait_for_service_ready(service_name)
        sys.exit(0 if success else 1)
    
    elif command == 'cleanup':
        coordinator.cleanup_coordination_data()
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
