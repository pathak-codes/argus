#!/usr/bin/env python3
"""
Security Scanner Launcher
Scans discovered web assets for hardcoded credentials, APIs, and .env files
"""

import sys
from security_scanner import run_security_scan

if __name__ == "__main__":
    print("\n" + "=" * 90)
    print("🔐 ARGUS SECURITY SCANNER")
    print("=" * 90)
    print("\nThis tool scans discovered web assets for:")
    print("  ✓ Hardcoded credentials (passwords, API keys, secrets)")
    print("  ✓ Exposed .env files")
    print("  ✓ API endpoints (Swagger, GraphQL, Admin panels)")
    print("  ✓ Tech stack disclosure")
    print("\nUsing multithreading for fast scanning...\n")
    
    # Get number of workers
    try:
        workers = int(input("Enter number of scanning threads (default 8): ") or "8")
    except:
        workers = 8
    
    run_security_scan(num_workers=workers)
