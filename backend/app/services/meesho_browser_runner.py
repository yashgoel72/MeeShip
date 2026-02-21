"""
Standalone Playwright script for Meesho login capture.
This runs as a separate process to avoid asyncio conflicts with uvicorn.

Based on working POC in scripts/meesho_playwright_poc.py

Usage:
    python meesho_browser_runner.py <output_file>
    
Writes JSON to output_file with captured credentials.
"""

import json
import sys
import time
import logging
import urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEESHO_LOGIN_URL = "https://supplier.meesho.com/panel/v3/new/root/login"
MEESHO_SUPPLIER_URL = "https://supplier.meesho.com"


def run_meesho_login(output_file: str):
    """Run Meesho login flow and capture credentials."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        result = {"success": False, "error": "Playwright not installed"}
        with open(output_file, 'w') as f:
            json.dump(result, f)
        return
    
    captured_supplier_id = None
    captured_identifier = None
    captured_connect_sid = None
    captured_browser_id = None
    
    try:
        with sync_playwright() as p:
            # Launch visible browser
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                ]
            )
            
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
            
            page = context.new_page()
            
            # Intercept requests to capture headers (as backup)
            def handle_request(request):
                nonlocal captured_supplier_id, captured_identifier
                
                if "catalogingapi" in request.url or "supplier.meesho.com" in request.url:
                    headers = request.headers
                    if "supplier-id" in headers and headers["supplier-id"]:
                        captured_supplier_id = headers["supplier-id"]
                        logger.info(f"Captured supplier-id from headers: {captured_supplier_id}")
                    if "identifier" in headers and headers["identifier"]:
                        captured_identifier = headers["identifier"]
                        logger.info(f"Captured identifier from headers: {captured_identifier}")
            
            page.on("request", handle_request)
            
            # Navigate to Meesho supplier login
            try:
                page.goto(MEESHO_LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                logger.warning(f"Initial navigation warning: {e}")
            
            logger.info("Navigated to Meesho login page - please log in...")
            
            # Wait for successful login - use same detection as POC
            login_success = False
            max_wait = 300  # 5 minutes max
            check_interval = 3
            waited = 0
            
            while waited < max_wait:
                time.sleep(check_interval)
                waited += check_interval
                
                current_url = page.url
                logger.info(f"[{waited}s] Current URL: {current_url}")
                
                # Detection method 1: URL changed to dashboard/panel (not login)
                if "/panel/" in current_url and "/login" not in current_url:
                    logger.info("✅ Dashboard URL detected!")
                    login_success = True
                    time.sleep(2)  # Let page fully load
                    break
                
                # Detection method 2: connect.sid cookie exists (backup - this is key!)
                cookies = context.cookies(MEESHO_SUPPLIER_URL)
                for cookie in cookies:
                    if cookie["name"] == "connect.sid":
                        logger.info(f"✅ connect.sid cookie found!")
                        login_success = True
                        time.sleep(2)
                        break
                
                if login_success:
                    break
                
                # Detection method 3: headers captured from API calls
                if captured_supplier_id and captured_identifier:
                    logger.info("✅ Login detected via captured headers!")
                    login_success = True
                    break
            
            if not login_success:
                result = {"success": False, "error": "Login timeout - please log in within 5 minutes"}
                browser.close()
                with open(output_file, 'w') as f:
                    json.dump(result, f)
                return
            
            logger.info("Login successful! Extracting credentials...")
            
            # Give time for cookies to be set
            time.sleep(3)
            
            # Get ALL cookies from the context (this is the key advantage of Playwright!)
            cookies = context.cookies(MEESHO_SUPPLIER_URL)
            logger.info(f"Found {len(cookies)} cookies")
            
            for cookie in cookies:
                cookie_name = cookie["name"]
                http_only = "🔒" if cookie.get("httpOnly") else "  "
                logger.info(f"  {http_only} {cookie_name}")
                
                # connect.sid - the session cookie (HttpOnly!)
                if cookie_name == "connect.sid":
                    captured_connect_sid = cookie["value"]
                    logger.info(f"    ✅ Captured connect.sid")
                
                # browser_id
                elif cookie_name == "browser_id":
                    captured_browser_id = cookie["value"]
                    logger.info(f"    ✅ Captured browser_id: {captured_browser_id}")
                
                # mixpanel cookie - contains supplier_id and identifier
                elif cookie_name.startswith("mp_a66867"):
                    try:
                        decoded = urllib.parse.unquote(cookie["value"])
                        data = json.loads(decoded)
                        
                        supplier_id = data.get("Supplier_id") or data.get("supplier_id")
                        identifier = data.get("Supplier_tag") or data.get("identifier")
                        
                        if supplier_id:
                            captured_supplier_id = str(supplier_id)
                            logger.info(f"    ✅ Captured supplier_id from mixpanel: {captured_supplier_id}")
                        if identifier:
                            captured_identifier = identifier
                            logger.info(f"    ✅ Captured identifier from mixpanel: {captured_identifier}")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"    ⚠️ Could not parse mixpanel cookie: {e}")
            
            # If we didn't get supplier_id from mixpanel, try navigating to catalogs
            if not captured_supplier_id or not captured_identifier:
                logger.info("Navigating to catalogs page to trigger API calls...")
                try:
                    page.goto("https://supplier.meesho.com/panel/v3/new/cataloging", wait_until="networkidle", timeout=30000)
                    time.sleep(3)
                except Exception as e:
                    logger.warning(f"Navigation to catalogs failed: {e}")
            
            browser.close()
            
            # Check we have everything
            if not captured_connect_sid:
                result = {"success": False, "error": "Could not capture connect.sid cookie"}
            elif not captured_supplier_id:
                result = {"success": False, "error": "Could not capture supplier_id - check mixpanel cookie"}
            elif not captured_identifier:
                result = {"success": False, "error": "Could not capture identifier - check mixpanel cookie"}
            else:
                result = {
                    "success": True,
                    "supplier_id": captured_supplier_id,
                    "identifier": captured_identifier,
                    "connect_sid": captured_connect_sid,
                    "browser_id": captured_browser_id,
                }
                logger.info(f"✅ Success! Captured credentials for supplier {captured_supplier_id}")
            
            with open(output_file, 'w') as f:
                json.dump(result, f)
                
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        result = {"success": False, "error": str(e)}
        with open(output_file, 'w') as f:
            json.dump(result, f)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python meesho_browser_runner.py <output_file>")
        sys.exit(1)
    
    output_file = sys.argv[1]
    run_meesho_login(output_file)
