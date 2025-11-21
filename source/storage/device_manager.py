#!/usr/bin/env python3
"""
Device Registry Manager - CLI Wrapper for YAML Device Registry

Sprint: 005-system-reliability (User Story 6)
Purpose: Provide CLI interface for managing device names in config/device_registry.yaml

Features:
- List devices with names and metadata
- Set and amend device names in YAML registry
- Recursive history update for device name changes in database
- CLI commands for device management

Note: This is a CLI wrapper around YAMLDeviceRegistry. The YAML file can also be edited
directly in any text editor for simpler device name customization.
"""

import argparse
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
except Exception:
    pass

from source.storage.yaml_device_registry import YAMLDeviceRegistry
from source.storage.manager import DatabaseManager

logger = logging.getLogger(__name__)


def main():
    """CLI entry point for device management commands."""
    parser = argparse.ArgumentParser(
        description='Manage device names in YAML registry (config/device_registry.yaml)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set device name in YAML registry
  python source/storage/device_manager.py --set-name hue:ABC123 "Living Room Sensor"
  
  # Amend device name in YAML (registry only)
  python source/storage/device_manager.py --amend-name hue:ABC123 "Kitchen Sensor"
  
  # Amend device name and update all historical database readings
  python source/storage/device_manager.py --amend-name hue:ABC123 "Kitchen Sensor" --recursive
  
  # List all devices from YAML registry
  python source/storage/device_manager.py --list-devices
  
  # List only Hue sensors
  python source/storage/device_manager.py --list-devices --type hue_sensor

Note: You can also edit config/device_registry.yaml directly in any text editor.
      Changes take effect immediately on the next collection.
        """
    )
    
    # Command options
    parser.add_argument(
        '--set-name',
        nargs=2,
        metavar=('UNIQUE_ID', 'NAME'),
        help='Set device name in YAML registry'
    )
    parser.add_argument(
        '--amend-name',
        nargs=2,
        metavar=('UNIQUE_ID', 'NAME'),
        help='Amend device name in YAML (optionally update DB history with --recursive)'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='When amending name, update all historical database readings (use with --amend-name)'
    )
    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='List all devices from YAML registry with names and metadata'
    )
    parser.add_argument(
        '--type',
        help='Filter devices by type (use with --list-devices)'
    )
    parser.add_argument(
        '--registry-path',
        default='config/device_registry.yaml',
        help='Path to YAML registry file (default: config/device_registry.yaml)'
    )
    parser.add_argument(
        '--db-path',
        default='data/readings.db',
        help='Path to database file for --recursive updates (default: data/readings.db)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize YAML device registry
    try:
        registry_path = Path(args.registry_path)
        yaml_registry = YAMLDeviceRegistry(registry_path)
    except Exception as e:
        print(f"ERROR: Failed to initialize YAML registry: {e}")
        sys.exit(1)
    
    # Execute commands
    if args.set_name:
        unique_id, name = args.set_name
        try:
            yaml_registry.set_device_name(unique_id, name)
            print(f"✓ Set device name in YAML: {unique_id} → '{name}'")
            print(f"  (Edit {args.registry_path} to change it)")
        except Exception as e:
            print(f"✗ Failed to set device name: {e}")
            sys.exit(1)
    
    elif args.amend_name:
        unique_id, name = args.amend_name
        
        # Update YAML registry
        try:
            yaml_registry.set_device_name(unique_id, name)
            print(f"✓ Amended device name in YAML: {unique_id} → '{name}'")
        except Exception as e:
            print(f"✗ Failed to amend device name in YAML: {e}")
            sys.exit(1)
        
        # If --recursive, also update database history
        if args.recursive:
            try:
                db_manager = DatabaseManager(args.db_path)
                conn = db_manager.conn
                
                cursor = conn.execute(
                    """UPDATE readings 
                       SET name = ?
                       WHERE device_id = ?""",
                    (name, unique_id)
                )
                readings_updated = cursor.rowcount
                conn.commit()
                db_manager.close()
                
                print(f"  Updated {readings_updated} historical database readings")
                
            except Exception as e:
                print(f"✗ Failed to update database history: {e}")
                sys.exit(1)
    
    elif args.list_devices:
        try:
            devices = yaml_registry.list_devices(device_type=args.type)
            
            if not devices:
                print("No devices found")
            else:
                print(f"\nFound {len(devices)} device(s) in {args.registry_path}:\n")
                print(f"{'Unique ID':<45} {'Type':<15} {'Name':<30} {'Location':<20}")
                print("-" * 110)
                
                for device in devices:
                    unique_id = device.get('unique_id', 'unknown')
                    device_type = device.get('device_type', 'unknown')
                    name = device.get('name', '(no name)')
                    location = device.get('location', '(no location)')
                    
                    print(f"{unique_id:<45} {device_type:<15} {name:<30} {location:<20}")
                
                print(f"\nNote: Edit {args.registry_path} directly to customize device names")
        
        except Exception as e:
            print(f"✗ Failed to list devices: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
