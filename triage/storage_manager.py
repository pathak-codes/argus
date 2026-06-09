import json
import os
import re
import threading
from datetime import datetime, timezone


class StorageManager:
    def __init__(self, base_dir="results"):
        self.base_dir = base_dir
        self.screenshots_dir = os.path.join(base_dir, "screenshots")
        self.metadata_dir = os.path.join(base_dir, "metadata")
        self.reports_dir = os.path.join(base_dir, "reports")
        self.logs_dir = os.path.join(base_dir, "logs")

        self._dedup_set = set()
        self._dedup_lock = threading.Lock()

        for d in [self.screenshots_dir, self.metadata_dir, self.reports_dir, self.logs_dir]:
            os.makedirs(d, exist_ok=True)

    @staticmethod
    def _safe_filename(host, port):
        safe = re.sub(r"[^a-zA-Z0-9.-]", "_", host)[:50]
        return f"{safe}_{port}"

    def is_duplicate(self, dedup_key):
        with self._dedup_lock:
            if dedup_key in self._dedup_set:
                return True
            self._dedup_set.add(dedup_key)
            return False

    def save_screenshot(self, result, screenshot_path):
        if not screenshot_path:
            return None

        basename = self._safe_filename(result.host, result.port)
        dst = os.path.join(self.screenshots_dir, f"{basename}.png")

        try:
            if screenshot_path != dst:
                os.rename(screenshot_path, dst)
            return dst
        except Exception as e:
            return screenshot_path

    def save_metadata(self, result, screenshot_path):
        basename = self._safe_filename(result.host, result.port)
        meta = result.dict()
        meta["screenshot"] = screenshot_path or ""
        meta["analyzed_at"] = datetime.now(timezone.utc).isoformat()
        meta["dedup_key"] = result.dedup_key()

        path = os.path.join(self.metadata_dir, f"{basename}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)
        return path

    def dedup_count(self):
        with self._dedup_lock:
            return len(self._dedup_set)
