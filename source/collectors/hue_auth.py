#!/usr/bin/env python3
"""
Philips Hue Bridge Authentication Module

Handles discovery and authentication with Philips Hue Bridge on local network.
Supports both automatic mDNS discovery and manual IP configuration.

Usage:
    python source/collectors/hue_auth.py
"""

import argparse
import sys
import time
import yaml
from pathlib import Path
from typing import Optional, Tuple

from source.utils.structured_logger import StructuredLogger

try:
    from phue import Bridge, PhueRegistrationException
except ImportError:
    print("ERROR: Required package 'phue' not installed")
    print("Run: pip install phue")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: Required package 'requests' not installed")
    print("Run: pip install requests")
    sys.exit(1)


def discover_bridge(logger: Optional[StructuredLogger] = None) -> Optional[str]:
    """
    Discover Hue Bridge on local network using Philips mDNS discovery service.
    
    Args:
        logger: Optional StructuredLogger instance for logging
        
    Returns:
        str: Bridge IP address if found, None otherwise
    """
    if logger:
        logger.info("Attempting automatic Bridge discovery via mDNS...")
    
    try:
        # Use Philips discovery service (N-UPnP)
        response = requests.get('https://discovery.meethue.com/', timeout=5)
        bridges = response.json()
        
        if bridges and len(bridges) > 0:
            bridge_ip = bridges[0]['internalipaddress']
            if logger:
                logger.info(f"Bridge discovered at IP: {bridge_ip}")
            return bridge_ip
        else:
            if logger:
                logger.warning("No Hue Bridge found via automatic discovery")
            return None
            
    except requests.RequestException as e:
        if logger:
            logger.error(f"Discovery failed: {e}")
        return None
    except (KeyError, ValueError) as e:
        if logger:
            logger.error(f"Failed to parse discovery response: {e}")
        return None


def get_bridge_ip(config_path: str = "config/config.yaml", logger: Optional[StructuredLogger] = None) -> Optional[str]:
    """
    Get Bridge IP from config or auto-discovery.
    
    Args:
        config_path: Path to configuration file
        logger: Optional StructuredLogger instance for logging
        
    Returns:
        str: Bridge IP address if found, None otherwise
    """
    # Try to load manual IP from config
    try:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                manual_ip = config.get('collectors', {}).get('hue', {}).get('bridge_ip')
                auto_discover = config.get('collectors', {}).get('hue', {}).get('auto_discover', True)
                
                if manual_ip and not auto_discover:
                    if logger:
                        logger.info(f"Using manual Bridge IP from config: {manual_ip}")
                    return manual_ip
    except Exception as e:
        if logger:
            logger.warning(f"Could not load config file: {e}")
    
    # Fall back to auto-discovery
    return discover_bridge(logger)


def authenticate_bridge(bridge_ip: str, wait_seconds: int = 60, logger: Optional[StructuredLogger] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Authenticate with Hue Bridge using button press method.
    
    Args:
        bridge_ip: IP address of the Hue Bridge
        wait_seconds: Timeout for button press (seconds)
        logger: Optional StructuredLogger instance for logging
        
    Returns:
        Tuple of (api_key, bridge_id) if successful, (None, None) otherwise
    """
    if logger:
        logger.info(f"Attempting to connect to Bridge at {bridge_ip}...")
    
    try:
        bridge = Bridge(bridge_ip)

        if logger:
            logger.info("=" * 70)
            if logger:
                logger.info("PRESS THE BUTTON ON YOUR HUE BRIDGE")
            if logger:
                logger.info(f"Waiting up to {wait_seconds}s for button press...")
            if logger:
                logger.info("Press it now; I'll keep trying to register.")
            if logger:
                logger.info("=" * 70)

        start = time.time()
        attempt = 0
        while time.time() - start < wait_seconds:
            try:
                attempt += 1
                bridge.connect()
                # Get API key (username) and Bridge ID via API
                api_key = getattr(bridge, 'username', None)
                bridge_id = 'unknown'
                try:
                    api = bridge.get_api()
                    if isinstance(api, dict):
                        bridge_id = api.get('config', {}).get('bridgeid', 'unknown')
                except Exception as e:
                    if logger:
                        logger.debug(f"Unable to fetch bridge id from API: {e}")

                if logger:
                    logger.info("Authentication successful!")
                    if logger:
                        logger.info(f"Bridge ID: {bridge_id}")
                return api_key, bridge_id
            except PhueRegistrationException:
                remaining = int(wait_seconds - (time.time() - start))
                if logger:
                    logger.info(f"Button not detected yet (attempt {attempt}). {remaining}s remaining...")
                time.sleep(2)

        if logger:
            logger.error("Timed out waiting for button press. Please press the Bridge button and try again.")
        return None, None
    except Exception as e:
        if logger:
            logger.error(f"Authentication failed: {e}")
        return None, None


def save_credentials(api_key: str, bridge_id: str, secrets_path: str = "config/secrets.yaml", logger: Optional[StructuredLogger] = None) -> bool:
    """
    Save API key and Bridge ID to secrets.yaml file.
    
    Args:
        api_key: Hue API key (username)
        bridge_id: Hue Bridge unique identifier
        secrets_path: Path to secrets file
        logger: Optional StructuredLogger instance for logging
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    secrets_file = Path(secrets_path)
    
    try:
        # Load existing secrets or create new structure
        if secrets_file.exists():
            with open(secrets_file, 'r') as f:
                secrets = yaml.safe_load(f) or {}
        else:
            secrets = {}
        
        # Update Hue credentials
        if 'hue' not in secrets:
            secrets['hue'] = {}
        
        secrets['hue']['api_key'] = api_key
        secrets['hue']['bridge_id'] = bridge_id
        
        # Write back to file
        secrets_file.parent.mkdir(parents=True, exist_ok=True)
        with open(secrets_file, 'w') as f:
            yaml.dump(secrets, f, default_flow_style=False)
        
        if logger:
            logger.info(f"Credentials saved to {secrets_path}")
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"Failed to save credentials: {e}")
        return False


def main():
    """Main authentication flow."""
    # Create a simple logger for CLI usage
    config = {'component': 'hue_auth'}
    logger = StructuredLogger(config)
    
    parser = argparse.ArgumentParser(
        description='Authenticate with Philips Hue Bridge',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-discover and authenticate
  python source/collectors/hue_auth.py
  
  # Use specific IP address
  python source/collectors/hue_auth.py --bridge-ip 192.168.1.100
        """
    )
    parser.add_argument(
        '--bridge-ip',
        help='Manual Bridge IP address (skips auto-discovery)',
        type=str
    )
    parser.add_argument(
        '--config',
        help='Path to config file',
        default='config/config.yaml'
    )
    parser.add_argument(
        '--secrets',
        help='Path to secrets file',
        default='config/secrets.yaml'
    )
    
    args = parser.parse_args()
    
    # Step 1: Get Bridge IP
    if args.bridge_ip:
        bridge_ip = args.bridge_ip
        if logger:
            logger.info(f"Using manual Bridge IP: {bridge_ip}")
    else:
        bridge_ip = get_bridge_ip(args.config, logger)
    
    if not bridge_ip:
        if logger:
            logger.error("Could not find Hue Bridge")
        if logger:
            logger.error("Try specifying IP manually with --bridge-ip")
        sys.exit(1)
    
    # Step 2: Authenticate
    api_key, bridge_id = authenticate_bridge(bridge_ip, logger=logger)
    
    if not api_key:
        if logger:
            logger.error("Authentication failed")
        sys.exit(1)
    
    # Step 3: Save credentials
    if save_credentials(api_key, bridge_id, args.secrets, logger):
        if logger:
            logger.info("✓ Authentication complete!")
        if logger:
            logger.info(f"✓ Credentials saved to {args.secrets}")
        if logger:
            logger.info("✓ You can now run the collector")
    else:
        if logger:
            logger.error("Failed to save credentials")
        sys.exit(1)


if __name__ == '__main__':
    main()
