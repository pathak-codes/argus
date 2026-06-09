import sys
from status_classifier import classify_status, priority_sort_key

class OutputFormatter:
    def __init__(self):
        self.indent = 0

    @staticmethod
    def _details(finding):
        status = finding.get("status")
        details = ""

        if status in (301, 302, 307, 308):
            loc = finding.get("redirect_location", "")
            if loc:
                details = f"-> {loc}"
            elif finding.get("redirect_chain"):
                last = finding["redirect_chain"][-1]
                details = f"-> {last.get('location', '')}"
        elif status == 200:
            details = finding.get("content_type", "no content-type") or "(empty)"
        elif status == 401:
            auth = finding.get("auth_scheme", "")
            details = f"Auth: {auth}" if auth else "Unauthorized"
        elif status == 403:
            details = "Forbidden"
            ct = finding.get("content_type", "")
            length = finding.get("content_length", 0)
            if ct:
                details += f" ({ct})"
            if length > 1000:
                details += f" [{length}b]"
        elif status == 404:
            details = "Not Found"
        elif status == 405:
            details = "Method Not Allowed"
        elif status in (500, 502, 503):
            details = {500: "Internal Server Error", 502: "Bad Gateway", 503: "Service Unavailable"}[status]
            length = finding.get("content_length", 0)
            if length > 1000:
                details += f" [{length}b]"
        elif status == 429:
            details = "Rate Limited"
        elif status == 0:
            details = finding.get("error", "Unknown Error")

        notes = finding.get("notes", [])
        if notes:
            details += f" | {'; '.join(notes)}"

        return details

    def display(self, findings, show_medium=True, interesting_only=False, show_all=False):
        filtered = []
        for f in findings:
            priority = f.get("priority", "LOW")
            if show_all:
                filtered.append(f)
            elif interesting_only:
                if priority == "HIGH":
                    filtered.append(f)
            elif show_medium:
                if priority in ("HIGH", "MEDIUM"):
                    filtered.append(f)

        if not filtered:
            print("[-] No findings match the current filter.", flush=True)
            return

        filtered.sort(key=lambda f: (priority_sort_key(f.get("status", 999)), f.get("ip", ""), f.get("port", "")))

        col_ip = max(18, max((len(f.get("ip", "")) for f in filtered), default=18))
        col_port = 6

        header = (
            f"{'IP':<{col_ip}} "
            f"{'PORT':<{col_port}} "
            f"{'STATUS':<7} "
            f"{'PRIORITY':<9} "
            f"{'METHOD':<8} "
            f"{'DETAILS'}"
        )
        sep = "=" * max(len(header), 90)

        print(sep, flush=True)
        print(header, flush=True)
        print(sep, flush=True)

        for f in filtered:
            priority = f.get("priority", "LOW")
            status = f.get("status", "ERR")
            if status == 0:
                status_display = "ERR"
            else:
                status_display = str(status)

            method = f.get("method", "GET")
            details = self._details(f)

            line = (
                f"{f.get('ip', ''):<{col_ip}} "
                f"{f.get('port', ''):<{col_port}} "
                f"{status_display:<7} "
                f"{priority:<9} "
                f"{method:<8} "
                f"{details}"
            )
            print(line.rstrip(), flush=True)

        print(sep, flush=True)
        print(f"[+] Displayed {len(filtered)} findings", flush=True)

    @staticmethod
    def print_summary(findings):
        status_counts = {}
        interesting_hosts = set()

        for f in findings:
            s = f.get("status")
            if s and s > 0:
                status_counts[s] = status_counts.get(s, 0) + 1
            p = f.get("priority", "LOW")
            if p in ("HIGH", "MEDIUM"):
                interesting_hosts.add(f"{f['ip']}:{f['port']}")

        redirects = sum(1 for f in findings if 300 <= f.get("status", 0) < 400)

        print()
        print("=" * 90)
        print("SCAN SUMMARY")
        print("=" * 90)

        for code in [200, 401, 403, 405, 500, 502, 503]:
            count = status_counts.get(code, 0)
            if count > 0:
                print(f"  {code}: {count}")

        print(f"  Redirects (3xx): {redirects}")
        print(f"  Interesting Hosts: {len(interesting_hosts)}")
        print(f"  Total Findings: {len(findings)}")
        print(flush=True)
