import sqlite3
import sys
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from status_classifier import classify_status, HIGH_STATUSES, MEDIUM_STATUSES

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_PATH = Path(__file__).parent / "assets.db"

DEFAULT_METHODS = ["GET", "HEAD", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"]
PROBE_METHODS = ["POST", "PUT", "DELETE", "PATCH", "TRACE"]


class HttpAnalyzer:
    def __init__(self, timeout=5, max_redirects=5, retries=2, workers=10):
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.retries = retries
        self.workers = workers
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()
        session.verify = False
        session.max_redirects = self.max_redirects

        retry_strategy = Retry(
            total=self.retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=50,
            pool_maxsize=50,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get_targets_from_db(self):
        db = str(DB_PATH)
        if not Path(db).exists():
            print("[-] assets.db not found. Run scanner_engine.py first.", flush=True)
            return []
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ip_address, port FROM web_assets")
        targets = cursor.fetchall()
        conn.close()
        if not targets:
            print("[-] No assets found in database.", flush=True)
        return targets

    @staticmethod
    def _build_url(host, port_str):
        clean_port = str(port_str).split("/")[0]
        protocol = "https" if "443" in str(port_str) else "http"
        return f"{protocol}://{host}:{clean_port}", clean_port

    def _send_request(self, method, url, timeout=None):
        t = timeout or self.timeout
        try:
            resp = self.session.request(
                method, url, timeout=t, allow_redirects=True,
            )

            redirect_chain = []
            for h in resp.history:
                redirect_chain.append({
                    "status": h.status_code,
                    "location": h.headers.get("Location", ""),
                    "url": h.url,
                })

            content_type = resp.headers.get("Content-Type", "")
            content_length = len(resp.content)
            auth_scheme = resp.headers.get("WWW-Authenticate", "")
            server = resp.headers.get("Server", "")

            finding = {
                "ip": "",
                "port": "",
                "url": url,
                "method": method.upper(),
                "status": resp.status_code,
                "content_type": content_type.split(";")[0].strip() if content_type else "",
                "content_length": content_length,
                "redirect_chain": redirect_chain,
                "redirect_count": len(redirect_chain),
                "final_url": resp.url,
                "priority": classify_status(resp.status_code),
                "auth_scheme": auth_scheme,
                "server": server,
                "notes": [],
            }

            if resp.history:
                last = resp.history[-1]
                finding["redirect_location"] = last.headers.get("Location", "")

            return finding

        except requests.exceptions.Timeout:
            return {"status": 0, "error": "Timeout", "notes": [], "content_length": 0}
        except requests.exceptions.ConnectionError:
            return {"status": 0, "error": "Connection Refused", "notes": [], "content_length": 0}
        except requests.exceptions.TooManyRedirects:
            return {"status": 0, "error": "Too Many Redirects", "notes": [], "content_length": 0}
        except Exception as e:
            msg = str(e)[:60]
            return {"status": 0, "error": msg, "notes": [], "content_length": 0}

    def _detect_interesting(self, findings, host, port):
        methods_with_status = {}
        for f in findings:
            m = f.get("method", "?")
            s = f.get("status", 0)
            methods_with_status[m] = s

        unique_statuses = set(v for v in methods_with_status.values() if v > 0)

        if len(unique_statuses) > 1:
            parts = sorted(f"{m}={s}" for m, s in methods_with_status.items() if s > 0)
            note = f"Multi-status: {', '.join(parts)}"
            for f in findings:
                if note not in f["notes"]:
                    f["notes"].append(note)

        for f in findings:
            s = f.get("status", 0)

            if s == 500 and f.get("content_length", 0) > 10000:
                f["notes"].append(f"Large 500 body: {f['content_length']}b")

            if s == 401 and f.get("auth_scheme"):
                f["notes"].append(f"Auth: {f['auth_scheme']}")

            if f.get("redirect_count", 0) > 3:
                chain = " -> ".join(
                    r["location"][:40] for r in f.get("redirect_chain", [])
                )
                f["notes"].append(f"Redirect chain ({f['redirect_count']} hops): {chain}")

            if s == 403:
                ct = f.get("content_type", "")
                if "html" in ct and f.get("content_length", 0) < 500:
                    f["notes"].append("Thin 403 – resource likely exists")

    def analyze_target(self, host, port_str):
        url, clean_port = self._build_url(host, port_str)
        findings = []

        get_result = self._send_request("GET", url)
        if get_result["status"] == 0:
            get_result["ip"] = host
            get_result["port"] = clean_port
            get_result["priority"] = classify_status(get_result["status"])
            return [get_result]

        get_result["ip"] = host
        get_result["port"] = clean_port
        findings.append(get_result)

        head_result = self._send_request("HEAD", url)
        if head_result["status"] > 0:
            head_result["ip"] = host
            head_result["port"] = clean_port
            if head_result["status"] != get_result["status"]:
                findings.append(head_result)

        opts_result = self._send_request("OPTIONS", url, timeout=3)
        if opts_result["status"] > 0:
            opts_result["ip"] = host
            opts_result["port"] = clean_port
            if opts_result["status"] != get_result["status"]:
                findings.append(opts_result)

        should_probe = (
            get_result["status"] in HIGH_STATUSES
            or get_result["status"] in MEDIUM_STATUSES
        )

        if should_probe:
            for method in PROBE_METHODS:
                result = self._send_request(method, url, timeout=4)
                if result["status"] > 0:
                    result["ip"] = host
                    result["port"] = clean_port
                    if result["status"] != get_result["status"]:
                        findings.append(result)

        self._detect_interesting(findings, host, clean_port)
        return findings

    def run(self, targets):
        if not targets:
            return []

        print(f"\n[+] Analyzing {len(targets)} targets with {self.workers} workers...\n", flush=True)

        all_findings = []
        completed = 0

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_map = {
                executor.submit(self.analyze_target, host, port): (host, port)
                for host, port in targets
            }

            for future in as_completed(future_map):
                completed += 1
                host, port = future_map[future]
                try:
                    result = future.result()
                    all_findings.extend(result)
                except Exception as e:
                    print(f"\n[-] Error on {host}:{port} — {str(e)[:60]}", flush=True)

                sys.stdout.write(f"\r[Progress] {completed}/{len(targets)} targets")
                sys.stdout.flush()

        sys.stdout.write("\n")
        sys.stdout.flush()
        return all_findings
