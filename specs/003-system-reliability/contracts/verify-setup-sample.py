#!/usr/bin/env python3
"""
System Health Check for Home Temperature Monitoring

Validates:
- Configuration files (config.yaml, secrets.yaml)
- Database write access and WAL mode
- Hue Bridge connectivity and authentication
- Sensor discovery

Exit codes:
    0 = All checks passed (system healthy)
    1 = One or more checks failed
    2 = Critical error (import failure, unexpected exception)

Usage:
    python source/verify_setup.py
    
    # Run before starting collection
    python source/verify_setup.py && python source/collectors/hue_collector.py --continuous
"""

import sys
import os
import sqlite3
import yaml
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class HealthCheck:
    """System health check coordinator."""
    
    def __init__(self):
        self.results = []
        self.start_time = None
    
    def run_all_checks(self) -> int:
        """
        Run all health checks.
        
        Returns:
            int: Exit code (0 = success, 1 = failure)
        """
        self.start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("🏥 SYSTEM HEALTH CHECK")
        logger.info("=" * 60)
        logger.info("")
        
        # Define checks in execution order
        checks = [
            ("Configuration", self.check_config),
            ("Secrets", self.check_secrets),
            ("Database", self.check_database),
            ("Hue Bridge", self.check_hue_bridge),
        ]
        
        # Run each check
        for component, check_fn in checks:
            try:
                success, message = check_fn()
                self.results.append((component, success, message))
                
                status_icon = "✅" if success else "❌"
                logger.info(f"{status_icon} {component}: {'PASS' if success else 'FAIL'}")
                logger.info(f"   {message}")
                logger.info("")
                
            except Exception as e:
                self.results.append((component, False, f"Unexpected error: {e}"))
                logger.info(f"❌ {component}: FAIL")
                logger.info(f"   Unexpected error: {e}")
                logger.info("")
        
        # Summary
        logger.info("=" * 60)
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        if passed == total:
            logger.info("📊 OVERALL STATUS: HEALTHY")
            logger.info(f"All {total} checks passed")
        else:
            logger.info("⚠️  OVERALL STATUS: UNHEALTHY")
            logger.info(f"{passed}/{total} checks passed, {total - passed} failed")
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"Completed in {elapsed:.1f}s")
        logger.info("=" * 60)
        
        return 0 if passed == total else 1
    
    def check_config(self) -> Tuple[bool, str]:
        """Validate config.yaml exists and has required keys."""
        config_path = "config/config.yaml"
        
        if not os.path.exists(config_path):
            return False, f"Config file not found: {config_path}"
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            return False, f"Invalid YAML: {e}"
        
        # Check required sections
        required_sections = ['collection', 'storage', 'logging', 'collectors']
        missing = [s for s in required_sections if s not in config]
        
        if missing:
            return False, f"Missing required sections: {', '.join(missing)}"
        
        # Check critical keys
        if not config.get('storage', {}).get('database_path'):
            return False, "Missing storage.database_path in config"
        
        return True, "Config file valid, all required keys present"
    
    def check_secrets(self) -> Tuple[bool, str]:
        """Validate secrets.yaml exists and has Hue API key."""
        secrets_path = "config/secrets.yaml"
        
        if not os.path.exists(secrets_path):
            return False, f"Secrets file not found: {secrets_path}. Run: python source/collectors/hue_auth.py"
        
        try:
            with open(secrets_path, 'r') as f:
                secrets = yaml.safe_load(f)
        except Exception as e:
            return False, f"Invalid YAML: {e}"
        
        # Check for Hue API key
        hue_secrets = secrets.get('hue', {})
        if not hue_secrets.get('api_key'):
            return False, "Missing hue.api_key in secrets.yaml. Run authentication: python source/collectors/hue_auth.py"
        
        return True, "Hue API key found"
    
    def check_database(self) -> Tuple[bool, str]:
        """Validate database write access and WAL mode."""
        # Load config for database path
        try:
            with open('config/config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            db_path = config.get('storage', {}).get('database_path', 'data/readings.db')
        except Exception as e:
            return False, f"Cannot load config: {e}"
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        try:
            # Connect to database
            conn = sqlite3.connect(db_path)
            
            # Check WAL mode
            cursor = conn.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0].upper()
            wal_enabled = journal_mode == "WAL"
            
            # Test write access
            test_table = "_health_check_test"
            conn.execute(f"CREATE TABLE IF NOT EXISTS {test_table} (id INTEGER)")
            conn.execute(f"INSERT INTO {test_table} (id) VALUES (1)")
            conn.execute(f"DELETE FROM {test_table}")
            conn.execute(f"DROP TABLE {test_table}")
            conn.commit()
            conn.close()
            
            wal_status = "WAL mode enabled" if wal_enabled else "WAL mode NOT enabled (will be enabled on first collection)"
            return True, f"Database write test successful ({wal_status})"
            
        except Exception as e:
            return False, f"Database error: {e}"
    
    def check_hue_bridge(self) -> Tuple[bool, str]:
        """Validate Hue Bridge connectivity and sensor discovery."""
        # Load config and secrets
        try:
            with open('config/config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            with open('config/secrets.yaml', 'r') as f:
                secrets = yaml.safe_load(f)
        except Exception as e:
            return False, f"Cannot load config/secrets: {e}"
        
        # Check if phue is available
        try:
            from phue import Bridge
        except ImportError:
            return False, "phue library not installed. Run: pip install phue"
        
        # Get connection details
        hue_config = config.get('collectors', {}).get('hue', {})
        hue_secrets = secrets.get('hue', {})
        
        bridge_ip = hue_config.get('bridge_ip')
        api_key = hue_secrets.get('api_key')
        
        if not api_key:
            return False, "No API key found. Run authentication: python source/collectors/hue_auth.py"
        
        try:
            # Connect to bridge
            if bridge_ip:
                bridge = Bridge(ip=bridge_ip, username=api_key)
            else:
                bridge = Bridge(ip=None, username=api_key)
            
            # Get sensors
            api_data = bridge.get_api()
            all_sensors = api_data.get('sensors', {})
            
            # Count temperature sensors
            temp_sensors = [
                s for s in all_sensors.values()
                if s.get('type') == 'ZLLTemperature'
            ]
            
            if not temp_sensors:
                return False, "No temperature sensors found on bridge"
            
            bridge_ip_actual = bridge.ip if hasattr(bridge, 'ip') else 'auto-discovered'
            return True, f"Connected to bridge {bridge_ip_actual}, {len(temp_sensors)} temperature sensor(s) discovered"
            
        except Exception as e:
            return False, f"Bridge connection failed: {e}"


def main():
    """Main entry point."""
    try:
        checker = HealthCheck()
        exit_code = checker.run_all_checks()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nHealth check interrupted by user")
        sys.exit(2)
    except Exception as e:
        logger.error(f"\n❌ CRITICAL ERROR: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()
