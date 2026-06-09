import os
import sys
import re
import threading
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "captured_screenshots"

_thread_local = threading.local()
_all_instances = []
_instances_lock = threading.Lock()


def init_browser():
    """Create a browser for the current thread (one per thread)."""
    if not hasattr(_thread_local, "browser") or _thread_local.browser is None:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        _thread_local.playwright = pw
        _thread_local.browser = browser
        with _instances_lock:
            _all_instances.append((pw, browser))
    return _thread_local.browser


def close_browser():
    """Close the current thread's browser."""
    if hasattr(_thread_local, "browser") and _thread_local.browser:
        try:
            _thread_local.browser.close()
        except Exception:
            pass
        _thread_local.browser = None
    if hasattr(_thread_local, "playwright") and _thread_local.playwright:
        try:
            _thread_local.playwright.stop()
        except Exception:
            pass
        _thread_local.playwright = None


def close_all_browsers():
    """Close every browser instance across all threads."""
    with _instances_lock:
        for pw, browser in _all_instances:
            try:
                browser.close()
            except Exception:
                pass
            try:
                pw.stop()
            except Exception:
                pass
        _all_instances.clear()


def capture_screenshot(ip_address, port, web_title):
    """
    Uses a thread-local headless browser to capture a screenshot.
    Saves the file as 'HOST_PORT.png'.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    protocol = "https" if "443" in port else "http"

    clean_port = port.split("/")[0]
    url = f"{protocol}://{ip_address}:{clean_port}"

    safe_host = re.sub(r'[^a-zA-Z0-9.-]', '_', ip_address)[:50]
    filename = f"{OUTPUT_DIR}/{safe_host}_{clean_port}.png"

    try:
        browser = init_browser()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        page.set_viewport_size({"width": 1280, "height": 720})

        page.goto(url, timeout=8000, wait_until="domcontentloaded")

        page.screenshot(path=filename)
        context.close()

        print(f"[OK] Screenshot captured: {safe_host}:{clean_port}", flush=True)
        sys.stdout.flush()
        return filename

    except Exception as e:
        error_msg = str(e).split('\n')[0][:50]
        print(f"[FAIL] {safe_host}:{clean_port} - {error_msg}", flush=True)
        sys.stdout.flush()
        return None
