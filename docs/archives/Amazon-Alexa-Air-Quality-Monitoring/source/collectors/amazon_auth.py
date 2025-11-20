import logging

logger = logging.getLogger(__name__)

from playwright.sync_api import sync_playwright
import time

def run_amazon_login():
    """
    Launches Playwright to log in to Amazon and retrieve cookies.
    Returns a dictionary of cookies or None if failed.
    """
    logger.info("Starting Amazon login flow via Playwright...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            logger.info("Navigating to Amazon UK...")
            page.goto("https://www.amazon.co.uk/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.co.uk%2F%3Fref_%3Dnav_ya_signin&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=gbflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&")
            
            logger.info("Waiting for user to log in...")
            
            try:
                page.wait_for_url("https://www.amazon.co.uk/?ref_=nav_ya_signin*", timeout=300000) # 5 minutes timeout
            except Exception:
                logger.warning("Timeout waiting for login redirect.")
                browser.close()
                return None

            logger.info("Login detected! Navigating to Alexa SPA to get CSRF token...")
            # Navigate to the Alexa SPA to ensure we get the 'csrf' cookie
            page.goto("https://alexa.amazon.co.uk/spa/index.html")
            
            # Wait for the page to load enough to set cookies
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                logger.warning("Timeout waiting for Alexa SPA load, proceeding anyway...")
            
            logger.info("Capturing cookies...")
            cookies = context.cookies()
            browser.close()
            
            # Convert to a simple dict
            cookie_dict = {c['name']: c['value'] for c in cookies}
            return cookie_dict

    except Exception as e:
        logger.error(f"Playwright error: {e}")
        return None
