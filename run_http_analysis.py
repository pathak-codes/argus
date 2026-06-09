#!/usr/bin/env python3
import argparse
import sys

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from http_analyzer import HttpAnalyzer
from output_formatter import OutputFormatter
from json_exporter import JsonExporter


def main():
    parser = argparse.ArgumentParser(
        description="ARGUS HTTP Status Code Analyzer — categorize and surface interesting web endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s                          # Show HIGH + MEDIUM (default)\n"
            "  %(prog)s --interesting-only      # Only HIGH\n"
            "  %(prog)s --show-all               # Everything including 404\n"
            "  %(prog)s --json -o report.json   # Export to JSON\n"
            "  %(prog)s --workers 20 --timeout 8 # Tune performance\n"
        ),
    )

    display = parser.add_argument_group("Display options")
    display.add_argument(
        "--interesting-only", "-i",
        action="store_true",
        help="Show only HIGH priority results",
    )
    display.add_argument(
        "--show-medium", "-m",
        action="store_true",
        default=True,
        help="Include MEDIUM priority results (default)",
    )
    display.add_argument(
        "--show-all", "-a",
        action="store_true",
        help="Display every status code including LOW",
    )

    output = parser.add_argument_group("Output options")
    output.add_argument(
        "--json", "-j",
        action="store_true",
        help="Export all findings as JSON",
    )
    output.add_argument(
        "--output", "-o",
        default="http_analysis.json",
        help="JSON output path (default: http_analysis.json)",
    )

    perf = parser.add_argument_group("Performance options")
    perf.add_argument(
        "--workers", "-w",
        type=int,
        default=10,
        help="Number of concurrent workers (default: 10)",
    )
    perf.add_argument(
        "--timeout", "-t",
        type=int,
        default=5,
        help="Request timeout in seconds (default: 5)",
    )
    perf.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Max retries per request (default: 2)",
    )

    args = parser.parse_args()

    if args.show_all:
        args.show_medium = True
        args.interesting_only = False
    elif args.interesting_only:
        args.show_medium = False

    analyzer = HttpAnalyzer(
        timeout=args.timeout,
        retries=args.retries,
        workers=args.workers,
    )

    targets = analyzer.get_targets_from_db()
    if not targets:
        sys.exit(1)

    findings = analyzer.run(targets)

    if not findings:
        print("[-] No findings collected.", flush=True)
        sys.exit(0)

    print(flush=True)

    formatter = OutputFormatter()
    formatter.display(
        findings,
        show_medium=args.show_medium,
        interesting_only=args.interesting_only,
        show_all=args.show_all,
    )

    if args.json:
        exporter = JsonExporter()
        exporter.build_report(findings, len(targets))
        path = exporter.export(args.output)
        print(f"[+] JSON report saved to: {path}", flush=True)

    formatter.print_summary(findings)


if __name__ == "__main__":
    main()
