#!/usr/bin/env python3
"""
YAML-Based Device Registry Manager

Sprint: 005-system-reliability (User Story 6 - Enhanced)
Purpose: Manage device names in a user-editable YAML file

Features:
- Auto-infer device names from location + device type
- Store names in config/device_registry.yaml for easy editing
- Persist metadata (first_seen, last_seen, model_info)
- No database dependency for device names
- Human-readable and version-control friendly

TODO:
- When refactoring registries code, use a software design pattern to allow easy swapping between different registry backends (YAML, DB, etc). such as Strategy Pattern or Factory Pattern, where there is a manager class that selects the appropriate registry implementation based on configuration.
- Add unit tests for YAMLDevice
"""

import logging
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from threading import Lock

logger = logging.getLogger(__name__)

# Default path to device registry YAML
DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "config" / "device_registry.yaml"


def infer_device_name(location: Optional[str], device_type: str, device_id: str) -> str:
    """
    Infer a human-readable device name from location and device type.
    
    Args:
        location: Device location (e.g., "Hall", "Living Room")
        device_type: Device type (e.g., "hue_sensor", "alexa_aqm", "nest_thermostat")
        device_id: Device unique ID (used as fallback if no location)
        
    Returns:
        str: Inferred name (e.g., "Hall Hue Sensor", "Living Room AQM")
        
    Examples:
        >>> infer_device_name("Hall", "hue_sensor", "hue:ABC123")
        "Hall Hue Sensor"
        >>> infer_device_name("Living Room", "alexa_aqm", "alexa:XYZ")
        "Living Room AQM"
        >>> infer_device_name(None, "nest_thermostat", "nest:123")
        "Nest Thermostat"
    """
    # Map device types to friendly short names
    type_mapping = {
        'hue_sensor': 'Hue Sensor',
        'alexa_aqm': 'AQM',
        'amazon_aqm': 'AQM',
        'nest_thermostat': 'Nest Thermostat',
        'weather_api': 'Weather Station'
    }
    
    friendly_type = type_mapping.get(device_type, device_type.replace('_', ' ').title())
    
    if location and location.strip():
        # Location exists: combine location + type
        return f"{location} {friendly_type}"
    else:
        # No location: use type only
        return friendly_type


class YAMLDeviceRegistry:
    """
    YAML-based device registry for managing custom device names.
    
    Stores device information in a human-editable YAML file at config/device_registry.yaml.
    Names are auto-inferred on first discovery but can be manually edited in the YAML file.
    """
    
    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize YAML device registry.
        
        Args:
            registry_path: Path to device registry YAML file (default: config/device_registry.yaml)
        """
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self._lock = Lock()  # Thread-safe file access
        self._ensure_registry_exists()
    
    def _ensure_registry_exists(self):
        """Create registry file with default structure if it doesn't exist."""
        if not self.registry_path.exists():
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            default_content = {
                '_comment': (
                    'Device Registry - Custom Device Names\n'
                    '\n'
                    'This file maps device IDs to human-readable names.\n'
                    'Names are automatically inferred from location + device type on first discovery.\n'
                    'You can edit these names manually - changes take effect immediately.\n'
                    '\n'
                    'Format:\n'
                    '  device_id:\n'
                    '    name: "Custom Name"\n'
                    '    location: "Location Name"\n'
                    '    device_type: "hue_sensor|alexa_aqm|nest_thermostat"\n'
                    '    model_info: "Model information (optional)"\n'
                    '    first_seen: "YYYY-MM-DD HH:MM:SS"\n'
                    '    last_seen: "YYYY-MM-DD HH:MM:SS"\n'
                ),
                'devices': {}
            }
            self._save_registry(default_content)
            logger.info(f"Created device registry at {self.registry_path}")
    
    def _load_registry(self) -> Dict:
        """Load device registry from YAML file."""
        try:
            with open(self.registry_path, 'r') as f:
                data = yaml.safe_load(f) or {}
                return data if isinstance(data, dict) else {'devices': {}}
        except Exception as e:
            logger.error(f"Failed to load device registry: {e}")
            return {'devices': {}}
    
    def _save_registry(self, data: Dict):
        """Save device registry to YAML file."""
        try:
            with open(self.registry_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        except Exception as e:
            logger.error(f"Failed to save device registry: {e}")
    
    def register_device(
        self,
        unique_id: str,
        device_type: str,
        location: Optional[str] = None,
        model_info: Optional[str] = None
    ) -> str:
        """
        Register a device and return its name (inferred or existing custom name).
        
        Args:
            unique_id: Unique device identifier (e.g., 'hue:ABC123')
            device_type: Device type ('hue_sensor', 'alexa_aqm', etc.)
            location: Device location
            model_info: Optional model information
            
        Returns:
            str: Device name (custom or inferred)
        """
        with self._lock:
            registry = self._load_registry()
            devices = registry.get('devices', {})
            
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            
            if unique_id in devices:
                # Update existing device
                device = devices[unique_id]
                device['last_seen'] = now
                
                # Update location if changed
                if location and device.get('location') != location:
                    device['location'] = location
                    # Re-infer name if it was auto-generated (equals old location + type)
                    old_inferred = infer_device_name(device.get('location'), device_type, unique_id)
                    if device.get('name') == old_inferred:
                        device['name'] = infer_device_name(location, device_type, unique_id)
                
                device_name = device['name']
            else:
                # New device - infer name
                inferred_name = infer_device_name(location, device_type, unique_id)
                
                devices[unique_id] = {
                    'name': inferred_name,
                    'location': location or '',
                    'device_type': device_type,
                    'model_info': model_info or '',
                    'first_seen': now,
                    'last_seen': now
                }
                
                device_name = inferred_name
                logger.info(f"Registered new device: {unique_id} → '{inferred_name}'")
            
            registry['devices'] = devices
            self._save_registry(registry)
            
            return device_name
    
    def get_device_name(self, unique_id: str) -> Optional[str]:
        """
        Get device name from registry.
        
        Args:
            unique_id: Unique device identifier
            
        Returns:
            str: Device name, or None if not found
        """
        registry = self._load_registry()
        devices = registry.get('devices', {})
        device = devices.get(unique_id)
        return device.get('name') if device else None
    
    def get_device_info(self, unique_id: str) -> Optional[Dict]:
        """
        Get complete device information.
        
        Args:
            unique_id: Unique device identifier
            
        Returns:
            dict: Device information, or None if not found
        """
        registry = self._load_registry()
        devices = registry.get('devices', {})
        device = devices.get(unique_id)
        
        if device:
            return {
                'unique_id': unique_id,
                **device
            }
        return None
    
    def set_device_name(self, unique_id: str, name: str) -> bool:
        """
        Set custom device name.
        
        Args:
            unique_id: Unique device identifier
            name: Custom name
            
        Returns:
            bool: True if successful
        """
        with self._lock:
            registry = self._load_registry()
            devices = registry.get('devices', {})
            
            if unique_id not in devices:
                logger.error(f"Device not found: {unique_id}")
                return False
            
            devices[unique_id]['name'] = name
            devices[unique_id]['last_seen'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            
            registry['devices'] = devices
            self._save_registry(registry)
            
            logger.info(f"Updated device name: {unique_id} → '{name}'")
            return True
    
    def list_devices(self, device_type: Optional[str] = None) -> list:
        """
        List all registered devices.
        
        Args:
            device_type: Optional filter by device type
            
        Returns:
            list: List of device dictionaries
        """
        registry = self._load_registry()
        devices = registry.get('devices', {})
        
        result = []
        for unique_id, device_data in devices.items():
            if device_type and device_data.get('device_type') != device_type:
                continue
            
            result.append({
                'unique_id': unique_id,
                **device_data
            })
        
        return sorted(result, key=lambda d: d['unique_id'])
    
    def update_device_location(self, unique_id: str, location: str) -> bool:
        """
        Update device location.
        
        Args:
            unique_id: Unique device identifier
            location: New location
            
        Returns:
            bool: True if successful
        """
        with self._lock:
            registry = self._load_registry()
            devices = registry.get('devices', {})
            
            if unique_id not in devices:
                logger.error(f"Device not found: {unique_id}")
                return False
            
            devices[unique_id]['location'] = location
            devices[unique_id]['last_seen'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            
            registry['devices'] = devices
            self._save_registry(registry)
            
            logger.info(f"Updated device location: {unique_id} → '{location}'")
            return True
