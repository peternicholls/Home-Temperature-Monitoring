#!/usr/bin/env python3
"""
Amazon Alexa Cookie Capture Module

Handles cookie capture from Amazon account using Playwright browser automation.
Stores cookies in secrets.yaml for API authentication.
"""

import logging
import yaml
import os
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class AmazonCookieCapture:
    """
    Captures Amazon/Alexa authentication cookies using browser automation.
    
    Features:
    - Interactive browser login (user provides credentials)
    - Automatic cookie extraction after successful login
    - CSRF token capture from Alexa SPA
    - Secure storage in secrets.yaml
    """
    
    def __init__(self, domain: str = "amazon.co.uk", headless: bool = False):
        """
        Initialize cookie capture.
        
        Args:
            domain: Amazon domain (amazon.com, amazon.co.uk, etc.)
            headless: Run browser in headless mode (default: False for interactive login)
        """
        self.domain = domain
        self.headless = headless
        self.cookies: Optional[Dict[str, str]] = None
    
    def capture_cookies(self, timeout: int = 300) -> Optional[Dict[str, str]]:
        """
        Launch browser and capture cookies after user login.
        
        Args:
            timeout: Maximum wait time for login (seconds, default: 300)
            
        Returns:
            dict: Cookie name/value pairs, or None if failed
        """
        try:
            logger.info("Starting Amazon cookie capture via Playwright...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context()
                page = context.new_page()
                
                # Navigate to Amazon login
                login_url = f"https://www.{self.domain}/ap/signin"
                logger.info(f"Opening login page: {login_url}")
                page.goto(login_url)
                
                logger.info("Waiting for user to log in...")
                logger.info(f"Timeout: {timeout} seconds")
                
                try:
                    # Wait for redirect to home page after successful login
                    page.wait_for_url(f"https://www.{self.domain}/*", timeout=timeout * 1000)
                    logger.info("Login successful! Detected redirect to homepage")
                    
                except Exception as e:
                    logger.error(f"Timeout waiting for login: {e}")
                    browser.close()
                    return None
                
                # Navigate to Alexa SPA to ensure CSRF token is set
                # Only transform domain if it's not already in alexa.* format
                if 'alexa' not in self.domain:
                    alexa_domain = self.domain.replace("amazon", "alexa.amazon")
                else:
                    alexa_domain = self.domain
                alexa_url = f"https://{alexa_domain}/spa/index.html"
                logger.info(f"Navigating to Alexa SPA: {alexa_url}")
                page.goto(alexa_url)
                
                try:
                    page.wait_for_load_state("networkidle", timeout=30000)
                except Exception:
                    logger.warning("Timeout waiting for Alexa SPA load, proceeding anyway...")
                
                # Capture all cookies
                logger.info("Capturing cookies...")
                cookies = context.cookies()
                browser.close()
                
                # Convert to simple dict
                cookie_dict = {c['name']: c['value'] for c in cookies}
                
                logger.info(f"Captured {len(cookie_dict)} cookies")
                logger.info(f"Cookie names: {list(cookie_dict.keys())}")
                
                # Check for essential cookies
                essential = ['session-id', 'session-token']
                missing = [c for c in essential if c not in cookie_dict]
                if missing:
                    logger.warning(f"Missing essential cookies: {missing}")
                
                self.cookies = cookie_dict
                return cookie_dict
                
        except Exception as e:
            logger.error(f"Error capturing cookies: {e}", exc_info=True)
            return None
    
    def save_to_secrets(self, secrets_path: str = "config/secrets.yaml") -> bool:
        """
        Save captured cookies to secrets.yaml file.
        
        Args:
            secrets_path: Path to secrets.yaml file
            
        Returns:
            bool: True if successful
        """
        if not self.cookies:
            logger.error("No cookies to save")
            return False
        
        try:
            # Load existing secrets
            secrets = {}
            if os.path.exists(secrets_path):
                with open(secrets_path, 'r') as f:
                    secrets = yaml.safe_load(f) or {}
            
            # Update Amazon AQM section
            if 'amazon_aqm' not in secrets:
                secrets['amazon_aqm'] = {}
            
            secrets['amazon_aqm']['cookies'] = self.cookies
            
            # Write back to file
            with open(secrets_path, 'w') as f:
                yaml.dump(secrets, f, default_flow_style=False)
            
            logger.info(f"Saved {len(self.cookies)} cookies to {secrets_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
            return False


def capture_amazon_cookies(domain: str = "amazon.co.uk", secrets_path: str = "config/secrets.yaml") -> bool:
    """
    Convenience function to capture and save Amazon cookies.
    
    Args:
        domain: Amazon domain (amazon.com, amazon.co.uk, etc.)
        secrets_path: Path to secrets.yaml file
        
    Returns:
        bool: True if successful
    """
    capturer = AmazonCookieCapture(domain=domain, headless=False)
    cookies = capturer.capture_cookies()
    
    if cookies:
        return capturer.save_to_secrets(secrets_path)
    
    return False


def run_amazon_login(domain: str = "amazon.co.uk") -> Optional[Dict[str, str]]:
    """
    Launches Playwright to log in to Amazon and retrieve cookies.
    Used by web interface for cookie capture.
    
    Args:
        domain: Amazon domain (default: amazon.co.uk)
        
    Returns:
        dict: Cookie name/value pairs, or None if failed
    """
    capturer = AmazonCookieCapture(domain=domain, headless=False)
    cookies = capturer.capture_cookies(timeout=300)
    
    if cookies:
        # Save to secrets.yaml
        capturer.save_to_secrets()
    
    return cookies


def validate_amazon_cookies(cookies: Dict[str, str]) -> tuple[bool, list[str]]:
    """
    Validate Amazon cookie structure and presence of required cookies.
    
    Args:
        cookies: Dictionary of cookie name/value pairs
        
    Returns:
        tuple: (is_valid, list of error messages)
    """
    errors = []
    
    if not cookies:
        errors.append("No cookies provided")
        return False, errors
    
    # Check for essential cookies
    essential_cookies = ['session-id', 'session-token']
    missing = [c for c in essential_cookies if c not in cookies]
    
    if missing:
        errors.append(f"Missing essential cookies: {', '.join(missing)}")
    
    # Check for empty cookie values
    empty = [name for name, value in cookies.items() if not value or value.strip() == '']
    if empty:
        errors.append(f"Empty cookie values: {', '.join(empty)}")
    
    # Warn if cookie count is low (expected ~18 cookies)
    if len(cookies) < 10:
        errors.append(f"Low cookie count: {len(cookies)} (expected ~18)")
        logger.warning(f"Only {len(cookies)} cookies found, authentication may fail")
    
    is_valid = len(errors) == 0
    
    if is_valid:
        logger.info(f"✅ Cookie validation passed ({len(cookies)} cookies)")
    else:
        logger.error(f"❌ Cookie validation failed: {'; '.join(errors)}")
    
    return is_valid, errors


def check_cookie_expiration(cookies: Dict[str, str]) -> tuple[bool, Optional[str]]:
    """
    Check if Amazon cookies are expired (approximate 24-hour window).
    Note: This is a heuristic check - actual expiration depends on Amazon's policies.
    
    Args:
        cookies: Dictionary of cookie name/value pairs
        
    Returns:
        tuple: (is_expired, warning_message)
    """
    import time
    from datetime import datetime, timedelta
    
    # Check for session-id-time cookie (contains expiration timestamp)
    if 'session-id-time' in cookies:
        try:
            session_time_str = cookies['session-id-time'].rstrip('l')  # Remove trailing 'l'
            session_timestamp = int(session_time_str)
            session_date = datetime.fromtimestamp(session_timestamp)
            
            # Check if session is older than 23 hours (warn before 24-hour expiration)
            age = datetime.now() - session_date
            if age > timedelta(hours=23):
                warning = f"Cookies are {age.seconds // 3600} hours old and may expire soon. Please refresh."
                logger.warning(warning)
                return True, warning
            
            logger.info(f"Cookies are {age.seconds // 3600} hours old (valid)")
            return False, None
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse session-id-time: {e}")
    
    # If we can't determine expiration, assume cookies are valid
    return False, "Cannot determine cookie age - proceeding anyway"


# CLI interface for cookie capture
if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Capture Amazon cookies for Alexa API authentication")
    parser.add_argument('--domain', default='amazon.co.uk', help='Amazon domain (default: amazon.co.uk)')
    parser.add_argument('--secrets', default='config/secrets.yaml', help='Path to secrets.yaml')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("Amazon Cookie Capture Tool")
    print("="*60)
    print("\nThis tool will:")
    print("1. Open a browser window")
    print("2. Wait for you to log in to Amazon")
    print("3. Capture authentication cookies")
    print("4. Save cookies to secrets.yaml")
    print("\nPlease log in when the browser opens...")
    print("="*60 + "\n")
    
    success = capture_amazon_cookies(domain=args.domain, secrets_path=args.secrets)
    
    if success:
        print("\n✅ Cookie capture successful!")
        print(f"Cookies saved to: {args.secrets}")
        print("\nYou can now run the collector:")
        print("  python -m source.collectors.amazon_collector")
    else:
        print("\n❌ Cookie capture failed!")
        print("Please check the logs for details.")

