import os
import sys
import threading

from playwright.sync_api import sync_playwright


_thread_local = threading.local()
_all_screenshot_instances = []
_screenshot_instances_lock = threading.Lock()


class ScreenshotManager:
    def __init__(self, output_dir, viewport_width=1280, viewport_height=720,
                 timeout=10000, max_workers=4):
        self.output_dir = output_dir
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.timeout = timeout
        self.max_workers = max_workers

    def start(self):
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_browser(self):
        if not hasattr(_thread_local, "browser") or _thread_local.browser is None:
            pw = sync_playwright().start()
            browser = pw.chromium.launch(
                headless=True,
                args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"],
            )
            _thread_local.playwright = pw
            _thread_local.browser = browser
            with _screenshot_instances_lock:
                _all_screenshot_instances.append((pw, browser))
        return _thread_local.browser

    def capture(self, url, filename):
        filepath = os.path.join(self.output_dir, filename)
        if os.path.exists(filepath):
            return filepath

        try:
            browser = self._get_browser()
            context = browser.new_context(
                ignore_https_errors=True,
                viewport={"width": self.viewport_width, "height": self.viewport_height},
            )
            page = context.new_page()
            page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
            page.screenshot(path=filepath, full_page=False)
            context.close()
            return filepath
        except Exception as e:
            error_msg = str(e).split("\n")[0][:60]
            print(f"  [FAIL] Screenshot: {filename} - {error_msg}", flush=True)
            return None

    @staticmethod
    def stop():
        with _screenshot_instances_lock:
            for pw, browser in _all_screenshot_instances:
                try:
                    browser.close()
                except Exception:
                    pass
                try:
                    pw.stop()
                except Exception:
                    pass
            _all_screenshot_instances.clear()
