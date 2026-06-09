#!/usr/bin/env python3
import argparse
import sys

from triage.scan_manager import ScanManager


def main():
    parser = argparse.ArgumentParser(
        description="ARGUS Content Triage System — intelligently filter, score, and screenshot web pages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    perf = parser.add_argument_group("Performance")
    perf.add_argument("--http-workers", type=int, default=10, help="HTTP analysis workers (default: 10)")
    perf.add_argument("--screenshot-workers", type=int, default=4, help="Screenshot workers (default: 4)")
    perf.add_argument("--timeout", type=int, default=5, help="HTTP request timeout in seconds (default: 5)")
    perf.add_argument("--screenshot-timeout", type=int, default=10000, help="Screenshot timeout in ms (default: 10000)")

    filter_grp = parser.add_argument_group("Filtering")
    filter_grp.add_argument("--min-score", type=int, default=3, help="Minimum content score to screenshot (default: 3)")
    filter_grp.add_argument("--min-length", type=int, default=1024, help="Minimum content length in bytes (default: 1024)")
    filter_grp.add_argument("--min-port-priority", type=int, default=0, help="Minimum port priority to scan (default: 0)")

    output = parser.add_argument_group("Output")
    output.add_argument("--output-dir", "-o", default="results", help="Output directory (default: results)")
    output.add_argument("--db", default="assets.db", help="Path to assets.db (default: assets.db)")

    args = parser.parse_args()

    mgr = ScanManager(
        http_workers=args.http_workers,
        screenshot_workers=args.screenshot_workers,
        http_timeout=args.timeout,
        screenshot_timeout=args.screenshot_timeout,
        min_score=args.min_score,
        min_content_length=args.min_length,
        base_dir=args.output_dir,
        min_port_priority=args.min_port_priority,
    )

    if not mgr.load_targets_from_db(args.db):
        sys.exit(1)

    try:
        mgr.run()
    except KeyboardInterrupt:
        print("\n[-] Interrupted by user.", flush=True)
    finally:
        mgr.cleanup()


if __name__ == "__main__":
    main()
