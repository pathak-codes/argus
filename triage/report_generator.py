import json
import threading
from datetime import datetime, timezone


class ReportGenerator:
    def __init__(self):
        self._lock = threading.Lock()
        self.total_targets = 0
        self.total_analyzed = 0
        self.total_filtered = 0
        self.screenshots_saved = 0
        self.duplicates_skipped = 0
        self.status_distribution = {}
        self.priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        self.interesting_hosts = set()
        self.errors = 0
        self.start_time = None
        self.end_time = None

    def record_analyzed(self, result):
        with self._lock:
            self.total_analyzed += 1
            s = result.status
            self.status_distribution[s] = self.status_distribution.get(s, 0) + 1

            if result.error:
                self.errors += 1
                return

    def record_meaningful(self, result):
        from .content_classifier import SAFE_SCREENSHOT_STATUSES

        with self._lock:
            self.total_filtered += 1
            s = result.status
            if s in SAFE_SCREENSHOT_STATUSES:
                self.priority_counts["HIGH"] = self.priority_counts.get("HIGH", 0) + 1
            else:
                self.priority_counts["MEDIUM"] = self.priority_counts.get("MEDIUM", 0) + 1
            self.interesting_hosts.add(f"{result.host}:{result.port}")

    def record_screenshot(self, saved=True):
        with self._lock:
            if saved:
                self.screenshots_saved += 1
            else:
                self.duplicates_skipped += 1

    def generate(self, output_dir):
        self.end_time = datetime.now(timezone.utc)

        duration = None
        requests_per_second = None
        if self.start_time:
            delta = (self.end_time - self.start_time).total_seconds()
            duration = round(delta, 2)
            if delta > 0 and self.total_analyzed > 0:
                requests_per_second = round(self.total_analyzed / delta, 2)

        report = {
            "scan_metadata": {
                "tool": "ARGUS Content Triage System",
                "timestamp": self.end_time.isoformat(),
                "duration_seconds": duration,
                "requests_per_second": requests_per_second,
            },
            "summary": {
                "total_targets": self.total_targets,
                "total_analyzed": self.total_analyzed,
                "meaningful_pages": self.total_filtered,
                "screenshots_saved": self.screenshots_saved,
                "duplicates_skipped": self.duplicates_skipped,
                "errors": self.errors,
                "interesting_hosts": len(self.interesting_hosts),
            },
            "status_distribution": {
                str(k): v for k, v in sorted(self.status_distribution.items())
            },
            "priority_distribution": self.priority_counts,
        }

        import os
        path = os.path.join(output_dir, "summary.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        return path
