import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from .target_queue import TargetQueue
from .http_analyzer import HttpAnalyzer
from .content_classifier import ContentClassifier
from .screenshot_manager import ScreenshotManager
from .storage_manager import StorageManager
from .report_generator import ReportGenerator


class ScanManager:
    def __init__(
        self,
        http_workers=10,
        screenshot_workers=4,
        http_timeout=5,
        screenshot_timeout=10000,
        min_score=3,
        min_content_length=1024,
        base_dir="results",
        min_port_priority=0,
    ):
        self.http_workers = http_workers
        self.screenshot_workers = screenshot_workers

        self.target_queue = TargetQueue(min_priority=min_port_priority)
        self.http_analyzer = HttpAnalyzer(timeout=http_timeout, max_retries=2)
        self.classifier = ContentClassifier(
            min_score=min_score, min_content_length=min_content_length
        )
        self.screenshot_mgr = ScreenshotManager(
            output_dir=os.path.join(base_dir, "screenshots"),
            timeout=screenshot_timeout,
            max_workers=screenshot_workers,
        )
        self.storage = StorageManager(base_dir=base_dir)
        self.reporter = ReportGenerator()

        self._screenshot_queue = []
        self._screenshot_lock = threading.Lock()

    def load_targets_from_db(self, db_path="assets.db"):
        import sqlite3

        db = Path(db_path)
        if not db.exists():
            db = Path(__file__).parent.parent / db_path
        if not db.exists():
            print(f"[-] {db_path} not found. Run scanner_engine.py first.", flush=True)
            return False

        conn = sqlite3.connect(str(db))
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ip_address, port FROM web_assets")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("[-] No targets found in database.", flush=True)
            return False

        self.target_queue.add_many(rows)
        self.reporter.total_targets = len(rows)
        print(f"[+] Loaded {len(rows)} targets from database.", flush=True)
        return True

    def _http_worker(self, worker_id):
        while True:
            target = self.target_queue.get(timeout=3)
            if target is None:
                break
            host, port = target

            result = self.http_analyzer.analyze(host, port)
            self.reporter.record_analyzed(result)

            if result.status == 0:
                continue

            if not self.classifier.should_analyze(result):
                continue

            if not self.classifier.is_error_or_default(result):
                if self.classifier.should_screenshot(result):
                    with self._screenshot_lock:
                        self._screenshot_queue.append(result)
                    self.reporter.record_meaningful(result)

            sys.stdout.write(f"\r[HTTP] {worker_id}: {host}:{port} -> {result.status}")
            sys.stdout.flush()

    def _process_screenshots(self):
        with self._screenshot_lock:
            batch = list(self._screenshot_queue)
            self._screenshot_queue.clear()

        if not batch:
            return

        print(f"\n[~] Capturing {len(batch)} screenshots with {self.screenshot_workers} workers...", flush=True)

        with ThreadPoolExecutor(max_workers=self.screenshot_workers) as executor:
            futures = {}
            for result in batch:
                dedup_key = result.dedup_key()
                if self.storage.is_duplicate(dedup_key):
                    self.reporter.record_screenshot(saved=False)
                    continue

                basename = self.storage._safe_filename(result.host, result.port)
                filename = f"{basename}.png"
                url = result.url

                future = executor.submit(self.screenshot_mgr.capture, url, filename)
                futures[future] = (result, filename, basename)

            for future in as_completed(futures):
                result, filename, basename = futures[future]
                try:
                    path = future.result()
                    if path:
                        final_path = self.storage.save_screenshot(result, path)
                        self.storage.save_metadata(result, final_path)
                        self.reporter.record_screenshot(saved=True)
                        print(f"  [OK] {basename}.png", flush=True)
                    else:
                        self.reporter.record_screenshot(saved=False)
                except Exception as e:
                    print(f"  [FAIL] {basename} - {str(e)[:60]}", flush=True)

    def run(self):
        self.reporter.start_time = datetime.now(timezone.utc)

        print("=" * 90, flush=True)
        print("  ARGUS Content Triage System", flush=True)
        print("=" * 90, flush=True)
        print(f"  Targets: {self.reporter.total_targets}", flush=True)
        print(f"  HTTP Workers: {self.http_workers}", flush=True)
        print(f"  Screenshot Workers: {self.screenshot_workers}", flush=True)
        print(f"  Min Score Threshold: {self.classifier.min_score}", flush=True)
        print(f"  Min Content Length: {self.classifier.min_content_length}b", flush=True)
        print("=" * 90, flush=True)

        self.screenshot_mgr.start()

        print(f"\n[~] Analyzing targets with {self.http_workers} HTTP workers...", flush=True)

        http_threads = []
        for i in range(self.http_workers):
            t = threading.Thread(target=self._http_worker, args=(i + 1,), daemon=True)
            t.start()
            http_threads.append(t)

        for t in http_threads:
            t.join()

        print(f"\n[+] HTTP analysis complete. Filtered {len(self._screenshot_queue)} meaningful pages.", flush=True)

        self._process_screenshots()

        report_path = self.storage.reports_dir
        summary_file = self.reporter.generate(report_path)

        print("\n" + "=" * 90, flush=True)
        print("  TRIAGE COMPLETE", flush=True)
        print("=" * 90, flush=True)
        print(f"  Total targets:     {self.reporter.total_targets}", flush=True)
        print(f"  Analyzed:          {self.reporter.total_analyzed}", flush=True)
        print(f"  Meaningful pages:  {self.reporter.total_filtered}", flush=True)
        print(f"  Screenshots saved: {self.reporter.screenshots_saved}", flush=True)
        print(f"  Duplicates skipped:{self.reporter.duplicates_skipped}", flush=True)
        print(f"  Interesting hosts: {len(self.reporter.interesting_hosts)}", flush=True)
        print(f"  Error count:       {self.reporter.errors}", flush=True)

        if self.reporter.start_time:
            dur = (datetime.now(timezone.utc) - self.reporter.start_time).total_seconds()
            print(f"  Duration:          {dur:.1f}s", flush=True)

        print(f"\n  Summary:           {summary_file}", flush=True)
        print(f"  Screenshots:       {self.storage.screenshots_dir}", flush=True)
        print(f"  Metadata:          {self.storage.metadata_dir}", flush=True)
        print("=" * 90, flush=True)

    def cleanup(self):
        self.http_analyzer.close()
        self.screenshot_mgr.stop()
