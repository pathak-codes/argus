import json
from datetime import datetime, timezone
from pathlib import Path

class JsonExporter:
    def __init__(self):
        self.output = {}

    def build_report(self, findings, target_count):
        status_counts = {}
        priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        interesting_hosts = set()

        for f in findings:
            s = f.get("status")
            if s:
                status_counts[str(s)] = status_counts.get(str(s), 0) + 1
            p = f.get("priority", "LOW")
            priority_counts[p] = priority_counts.get(p, 0) + 1
            if p in ("HIGH", "MEDIUM"):
                interesting_hosts.add(f"{f['ip']}:{f['port']}")

        redirects = [f for f in findings if 300 <= f.get("status", 0) < 400]

        self.output = {
            "scan_metadata": {
                "tool": "ARGUS HTTP Analyzer",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_targets": target_count,
                "total_findings": len(findings),
                "interesting_hosts": len(interesting_hosts),
            },
            "summary": {
                "status_code_distribution": dict(sorted(status_counts.items())),
                "priority_distribution": priority_counts,
                "redirect_count": len(redirects),
            },
            "findings": findings,
        }

    def export(self, filepath):
        path = Path(filepath)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.output, f, indent=2, default=str)
        return str(path.resolve())
