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

            # Intercept requests to capture headers (backup method)
            def handle_request(request):
                nonlocal captured_supplier_id, captured_identifier
                if "catalogingapi" in request.url or "supplier.meesho.com" in request.url:
                    headers = request.headers
                    if headers.get("supplier-id"):
                        captured_supplier_id = headers["supplier-id"]
                        logger.info(f"Captured supplier-id from request headers: {captured_supplier_id}")
                    if headers.get("identifier"):
                        captured_identifier = headers["identifier"]
                        logger.info(f"Captured identifier from request headers: {captured_identifier}")

            # Intercept responses to capture supplier_id from API response bodies
            def handle_response(response):
                nonlocal captured_supplier_id, captured_identifier
                url = response.url
                try:
                    # Check login API response
                    if "v2-login" in url or "v2_login" in url or "login" in url:
                        if response.status == 200 and "application/json" in (response.headers.get("content-type") or ""):
                            body = response.json()
                            logger.info(f"Login API response keys: {list(body.keys()) if isinstance(body, dict) else 'not-dict'}")
                            if isinstance(body, dict):
                                sid = body.get("supplier_id") or body.get("supplierId") or body.get("Supplier_id")
                                if sid:
                                    captured_supplier_id = str(sid)
                                    logger.info(f"✅ Captured supplier_id from login response: {captured_supplier_id}")
                                ident = body.get("identifier") or body.get("Identifier")
                                if ident:
                                    captured_identifier = str(ident)
                                    logger.info(f"✅ Captured identifier from login response: {captured_identifier}")
                                # Check nested data
                                data = body.get("data") or body.get("result") or {}
                                if isinstance(data, dict):
                                    logger.info(f"Login response nested keys: {list(data.keys())}")
                                    sid2 = data.get("supplier_id") or data.get("supplierId") or data.get("Supplier_id") or data.get("id")
                                    if sid2 and not captured_supplier_id:
                                        captured_supplier_id = str(sid2)
                                        logger.info(f"✅ Captured supplier_id from login response data: {captured_supplier_id}")
                                    ident2 = data.get("identifier") or data.get("Identifier")
                                    if ident2 and not captured_identifier:
                                        captured_identifier = str(ident2)
                                        logger.info(f"✅ Captured identifier from login response data: {captured_identifier}")
                    # Check cataloging API responses
                    elif "catalogingapi" in url or "api/container" in url or "api/supplier" in url:
                        if response.status == 200 and "application/json" in (response.headers.get("content-type") or ""):
                            body = response.json()
                            if isinstance(body, dict):
                                sid = body.get("supplier_id") or body.get("supplierId")
                                if sid and not captured_supplier_id:
                                    captured_supplier_id = str(sid)
                                    logger.info(f"✅ Captured supplier_id from API response: {captured_supplier_id}")
                except Exception:
                    pass  # Don't crash on response parsing errors

            page.on("request", handle_request)
            page.on("response", handle_response)

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
            time.sleep(3)  # Let cookies settle

            # ── Extract credentials from cookies ────────────────────
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
                elif name.startswith("mp_a66867"):
                    logger.info(f"Found mixpanel cookie: {name}")
                    try:
                        decoded = urllib.parse.unquote(cookie["value"])
                        data = json.loads(decoded)
                        logger.info(f"Mixpanel cookie keys: {list(data.keys())}")
                        sid = data.get("Supplier_id") or data.get("supplier_id")
                        ident = data.get("Supplier_tag") or data.get("identifier")
                        if sid:
                            captured_supplier_id = str(sid)
                            logger.info(f"✅ Captured supplier_id from cookie: {captured_supplier_id}")
                        else:
                            logger.warning("No Supplier_id or supplier_id in mixpanel cookie")
                        if ident:
                            captured_identifier = ident
                            logger.info(f"✅ Captured identifier from cookie: {captured_identifier}")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Could not parse mixpanel cookie: {e}")

            # Fallback: navigate to catalogs page to trigger API calls
            if not captured_supplier_id or not captured_identifier:
                logger.info("Navigating to catalogs page to trigger API calls...")
                try:
                    page.goto(
                        "https://supplier.meesho.com/panel/v3/new/cataloging",
                        wait_until="networkidle", timeout=30000,
                    )
                    logger.info("Catalog page loaded (networkidle)")
                except Exception as e:
                    logger.warning(f"Navigation to catalogs: {e}")

                # Poll cookies for up to 10s waiting for supplier_id to appear
                poll_start = time.time()
                while not captured_supplier_id and (time.time() - poll_start) < 10:
                    time.sleep(1)
                    ck = context.cookies(MEESHO_SUPPLIER_URL)
                    for c in ck:
                        if c["name"].startswith("mp_a66867") or c["name"].startswith("mp_"):
                            try:
                                decoded = urllib.parse.unquote(c["value"])
                                data = json.loads(decoded)
                                sid = data.get("Supplier_id") or data.get("supplier_id")
                                if sid:
                                    captured_supplier_id = str(sid)
                                    logger.info(f"✅ Captured supplier_id from cookie (poll): {captured_supplier_id}")
                                ident = data.get("Supplier_tag") or data.get("identifier")
                                if ident and not captured_identifier:
                                    captured_identifier = ident
                                    logger.info(f"✅ Captured identifier from cookie (poll): {captured_identifier}")
                            except (json.JSONDecodeError, KeyError):
                                pass
                    if captured_supplier_id:
                        break
                    logger.info(f"Polling for supplier_id... ({int(time.time() - poll_start)}s)")

            # Fallback: call getSupplierDetails API directly via fetch
            if not captured_supplier_id and captured_identifier:
                logger.info(f"Calling getSupplierDetails API with identifier={captured_identifier}...")
                try:
                    api_result = page.evaluate("""
                        async (identifier) => {
                            try {
                                const resp = await fetch('/api/container/supplier/getSupplierDetails', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ identifier }),
                                });
                                if (!resp.ok) return { error: `HTTP ${resp.status}` };
                                const data = await resp.json();
                                return data;
                            } catch (e) {
                                return { error: e.message };
                            }
                        }
                    """, captured_identifier)
                    logger.info(f"getSupplierDetails response keys: {list(api_result.keys()) if isinstance(api_result, dict) else 'not-dict'}")
                    if isinstance(api_result, dict):
                        supplier = api_result.get("supplier", {})
                        if isinstance(supplier, dict):
                            sid = supplier.get("supplier_id")
                            if sid:
                                captured_supplier_id = str(sid)
                                logger.info(f"✅ Captured supplier_id from getSupplierDetails: {captured_supplier_id}")
                            if not captured_identifier:
                                ident = supplier.get("identifier")
                                if ident:
                                    captured_identifier = str(ident)
                                    logger.info(f"✅ Captured identifier from getSupplierDetails: {captured_identifier}")
                        elif api_result.get("error"):
                            logger.warning(f"getSupplierDetails error: {api_result['error']}")
                except Exception as e:
                    logger.warning(f"getSupplierDetails call failed: {e}")

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
        time.sleep(5)
        if not page.query_selector_all("input"):
            logger.error("No input fields found on login page")
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
