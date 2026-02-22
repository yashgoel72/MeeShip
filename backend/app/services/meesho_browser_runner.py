"""
Standalone Playwright script for Meesho login capture.
This runs as a separate process to avoid asyncio conflicts with uvicorn.

Supports TWO modes:
  1. PROGRAMMATIC (default):  Receives email + password as args, fills the form
                              automatically. Uses headed mode (with Xvfb on Azure)
                              to bypass Akamai bot detection.
  2. MANUAL (legacy):        Opens browser for user to type credentials manually.

Usage:
    # Programmatic mode
    python meesho_browser_runner.py <output_file> --email <email> --password <pw>

    # Manual mode (legacy)
    python meesho_browser_runner.py <output_file>

Writes JSON to output_file with captured credentials.
"""

import argparse
import json
import sys
import time
import logging
import urllib.parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEESHO_LOGIN_URL = "https://supplier.meesho.com/panel/v3/new/root/login"
MEESHO_SUPPLIER_URL = "https://supplier.meesho.com"


def run_meesho_login(output_file: str, email: str = None, password: str = None):
    """Run Meesho login flow and capture credentials.

    If *email* and *password* are provided the form is filled automatically
    (programmatic mode).  Otherwise a visible browser opens for the user to
    log in manually (legacy mode).
    """
    programmatic = bool(email and password)
    logger.info(f"Starting Meesho login in {'PROGRAMMATIC' if programmatic else 'MANUAL'} mode")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _write_result(output_file, {"success": False, "error": "Playwright not installed"})
        return

    captured_supplier_id = None
    captured_identifier = None
    captured_connect_sid = None
    captured_browser_id = None

    try:
        with sync_playwright() as p:
            # Always use headed mode — Akamai blocks headless Chromium.
            # On Azure Linux, Xvfb provides a virtual display.
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-size=1280,900",
                ]
            )

            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            )

            page = context.new_page()

            # Stealth: mask Playwright/automation signals
            page.add_init_script("""
                // Remove webdriver flag
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                // Remove chrome.runtime to avoid detection
                if (window.chrome) {
                    window.chrome.runtime = undefined;
                }
            """)

            # Navigate to Meesho supplier login
            try:
                page.goto(MEESHO_LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                logger.warning(f"Initial navigation warning: {e}")

            logger.info("Navigated to Meesho login page")

            # ── Login ───────────────────────────────────────────────
            if programmatic:
                login_success = _do_programmatic_login(page, context, email, password)
            else:
                login_success = _wait_for_manual_login(page, context)

            if not login_success:
                _write_result(output_file, {"success": False, "error": "Login failed or timed out"})
                browser.close()
                return

            logger.info("Login successful! Extracting credentials...")
            time.sleep(2)  # Brief pause for cookies to set

            # ── Step 1: Extract connect.sid & browser_id from cookies (always available) ──
            cookies = context.cookies(MEESHO_SUPPLIER_URL)
            logger.info(f"Found {len(cookies)} cookies")

            for cookie in cookies:
                name = cookie["name"]
                if name == "connect.sid":
                    captured_connect_sid = cookie["value"]
                    logger.info("✅ Captured connect.sid")
                elif name == "browser_id":
                    captured_browser_id = cookie["value"]
                    logger.info(f"✅ Captured browser_id: {captured_browser_id}")

            # ── Step 2: Call /api/container/supplier/getUser (most reliable) ──
            if not captured_supplier_id or not captured_identifier:
                logger.info("Calling /api/container/supplier/getUser...")
                try:
                    api_result = page.evaluate("""
                        async () => {
                            try {
                                const resp = await fetch('/api/container/supplier/getUser', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json;charset=UTF-8' },
                                    body: JSON.stringify({}),
                                    credentials: 'include',
                                });
                                if (!resp.ok) return { error: `HTTP ${resp.status}` };
                                return await resp.json();
                            } catch (e) {
                                return { error: e.message };
                            }
                        }
                    """)
                    logger.info(f"getUser response keys: {list(api_result.keys()) if isinstance(api_result, dict) else type(api_result)}")

                    if isinstance(api_result, dict) and not api_result.get("error"):
                        suppliers = api_result.get("suppliers", [])
                        if suppliers and isinstance(suppliers, list) and len(suppliers) > 0:
                            supplier = suppliers[0]
                            sid = supplier.get("supplier_id")
                            ident = supplier.get("identifier")
                            if sid:
                                captured_supplier_id = str(sid)
                                logger.info(f"✅ Captured supplier_id from getUser: {captured_supplier_id}")
                            if ident:
                                captured_identifier = str(ident)
                                logger.info(f"✅ Captured identifier from getUser: {captured_identifier}")
                        else:
                            logger.warning(f"getUser returned empty suppliers. Response: {json.dumps(api_result)[:500]}")
                    elif isinstance(api_result, dict):
                        logger.warning(f"getUser error: {api_result.get('error')}")
                except Exception as e:
                    logger.warning(f"getUser call failed: {e}")

            # ── Step 3: Fallback — Mixpanel cookie ──
            if not captured_supplier_id or not captured_identifier:
                logger.info("Trying mixpanel cookie fallback...")
                for cookie in cookies:
                    if cookie["name"].startswith("mp_a66867"):
                        try:
                            decoded = urllib.parse.unquote(cookie["value"])
                            data = json.loads(decoded)
                            sid = data.get("Supplier_id") or data.get("supplier_id")
                            if sid and not captured_supplier_id:
                                captured_supplier_id = str(sid)
                                logger.info(f"✅ Captured supplier_id from mixpanel cookie: {captured_supplier_id}")
                            ident = data.get("Supplier_tag") or data.get("identifier")
                            if ident and not captured_identifier:
                                captured_identifier = str(ident)
                                logger.info(f"✅ Captured identifier from mixpanel cookie: {captured_identifier}")
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"Could not parse mixpanel cookie: {e}")

            # ── Step 4: Last resort — navigate to catalogs and retry getUser ──
            if not captured_supplier_id or not captured_identifier:
                logger.info("Navigating to catalogs page and retrying getUser...")
                try:
                    page.goto(
                        "https://supplier.meesho.com/panel/v3/new/cataloging",
                        wait_until="networkidle", timeout=30000,
                    )
                    logger.info("Catalog page loaded (networkidle)")
                    time.sleep(2)

                    api_result = page.evaluate("""
                        async () => {
                            try {
                                const resp = await fetch('/api/container/supplier/getUser', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json;charset=UTF-8' },
                                    body: JSON.stringify({}),
                                    credentials: 'include',
                                });
                                if (!resp.ok) return { error: `HTTP ${resp.status}` };
                                return await resp.json();
                            } catch (e) {
                                return { error: e.message };
                            }
                        }
                    """)
                    if isinstance(api_result, dict) and not api_result.get("error"):
                        suppliers = api_result.get("suppliers", [])
                        if suppliers and isinstance(suppliers, list) and len(suppliers) > 0:
                            supplier = suppliers[0]
                            sid = supplier.get("supplier_id")
                            ident = supplier.get("identifier")
                            if sid and not captured_supplier_id:
                                captured_supplier_id = str(sid)
                                logger.info(f"✅ Captured supplier_id from getUser (retry): {captured_supplier_id}")
                            if ident and not captured_identifier:
                                captured_identifier = str(ident)
                                logger.info(f"✅ Captured identifier from getUser (retry): {captured_identifier}")
                        else:
                            logger.warning(f"getUser retry returned empty suppliers. Response: {json.dumps(api_result)[:500]}")
                    elif isinstance(api_result, dict):
                        logger.warning(f"getUser retry error: {api_result.get('error')}")
                except Exception as e:
                    logger.warning(f"getUser retry failed: {e}")

            browser.close()

            # Build result
            if not captured_connect_sid:
                result = {"success": False, "error": "Could not capture connect.sid cookie"}
            elif not captured_supplier_id:
                result = {"success": False, "error": "Could not capture supplier_id"}
            elif not captured_identifier:
                result = {"success": False, "error": "Could not capture identifier"}
            else:
                result = {
                    "success": True,
                    "supplier_id": captured_supplier_id,
                    "identifier": captured_identifier,
                    "connect_sid": captured_connect_sid,
                    "browser_id": captured_browser_id,
                }
                logger.info(f"✅ Captured credentials for supplier {captured_supplier_id}")

            _write_result(output_file, result)

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        _write_result(output_file, {"success": False, "error": str(e)})


# ============================================================================
# Login helpers
# ============================================================================

def _do_programmatic_login(page, context, email: str, password: str) -> bool:
    """Fill the Meesho login form and submit — no user interaction needed."""
    logger.info("Programmatic login: waiting for form...")

    # Wait for React form to render
    try:
        page.wait_for_selector("input", timeout=15000)
    except Exception:
        logger.warning("Form slow to render, extra wait...")
        time.sleep(3)
        if not page.query_selector_all("input"):
            # Debug: log page state
            logger.warning(f"Page title: {page.title()}")
            logger.warning(f"Page URL: {page.url}")
            try:
                page.screenshot(path="/tmp/login_debug.png")
                logger.info("Debug screenshot saved to /tmp/login_debug.png")
            except Exception:
                pass

            # Retry: reload page and wait again
            logger.info("Retrying: reloading login page...")
            try:
                page.reload(wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
                page.wait_for_selector("input", timeout=20000)
                logger.info("✅ Form appeared after reload")
            except Exception:
                time.sleep(5)
                if not page.query_selector_all("input"):
                    logger.error("No input fields found even after reload")
                    try:
                        page.screenshot(path="/tmp/login_debug_retry.png")
                    except Exception:
                        pass
                    return False

    # Fill email / phone
    for sel in ['input[name="emailOrPhone"]', 'input[type="email"]',
                'input[name="email"]', 'input[type="text"]', 'input[type="tel"]']:
        try:
            if page.query_selector(sel):
                page.fill(sel, email)
                logger.info(f"Email filled ({sel})")
                break
        except Exception:
            continue
    else:
        logger.error("Could not find email field")
        return False

    time.sleep(0.5)

    # Fill password
    for sel in ['input[name="password"]', 'input[type="password"]']:
        try:
            if page.query_selector(sel):
                page.fill(sel, password)
                logger.info(f"Password filled ({sel})")
                break
        except Exception:
            continue
    else:
        logger.error("Could not find password field")
        return False

    time.sleep(0.5)

    # Click submit
    for sel in ['button[type="submit"]', 'button:has-text("Login")',
                'button:has-text("Log In")', 'button:has-text("Continue")']:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click()
                logger.info(f"Submit clicked ({sel})")
                break
        except Exception:
            continue
    else:
        page.keyboard.press("Enter")
        logger.info("Pressed Enter as submit fallback")

    return _poll_for_login(page, context, timeout=30)


def _wait_for_manual_login(page, context) -> bool:
    """Wait for user to manually log in (legacy mode, 5-min timeout)."""
    logger.info("Please log in manually in the browser window...")
    return _poll_for_login(page, context, timeout=300)


def _poll_for_login(page, context, timeout: int) -> bool:
    """Poll for login success (URL change or connect.sid cookie)."""
    waited = 0
    while waited < timeout:
        time.sleep(2)
        waited += 2

        url = page.url
        if waited % 10 == 0:
            logger.info(f"[{waited}s] URL: {url}")

        if "/panel/" in url and "/login" not in url:
            logger.info("✅ Dashboard URL detected!")
            time.sleep(2)
            return True

        cookies = context.cookies(MEESHO_SUPPLIER_URL)
        if any(c["name"] == "connect.sid" for c in cookies):
            logger.info("✅ connect.sid cookie found!")
            time.sleep(2)
            return True

    logger.error(f"Login timed out after {timeout}s")
    return False


def _write_result(output_file: str, result: dict):
    """Write result JSON to the output file."""
    with open(output_file, "w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Meesho login capture")
    parser.add_argument("output_file", help="Path to write JSON result")
    parser.add_argument("--email", help="Meesho email for programmatic login")
    parser.add_argument("--password", help="Meesho password for programmatic login")
    args = parser.parse_args()

    run_meesho_login(args.output_file, email=args.email, password=args.password)
