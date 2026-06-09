import sqlite3
import requests
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urljoin

# Disable SSL warnings for self-signed certs
requests.packages.urllib3.disable_warnings()

DB_NAME = "assets.db"

def init_security_db():
    """Create security findings table."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                port TEXT,
                finding_type TEXT,
                finding_content TEXT,
                severity TEXT,
                discovered_at TIMESTAMP
            )
        """)
        conn.commit()

def check_env_file(host, port):
    """Check for .env files in root directory."""
    protocol = "https" if "443" in str(port) else "http"
    urls_to_check = [
        f"{protocol}://{host}:{port}/.env",
        f"{protocol}://{host}:{port}/.env.local",
        f"{protocol}://{host}:{port}/.env.example",
    ]
    
    findings = []
    for url in urls_to_check:
        try:
            response = requests.get(url, timeout=5, verify=False, allow_redirects=False)
            if response.status_code == 200:
                findings.append({
                    'type': 'ENV_FILE_FOUND',
                    'url': url,
                    'severity': 'CRITICAL',
                    'content': response.text[:200]
                })
        except:
            pass
    
    return findings

def check_hardcoded_credentials(host, port):
    """Scan for hardcoded credentials patterns."""
    protocol = "https" if "443" in str(port) else "http"
    url = f"{protocol}://{host}:{port}"
    
    findings = []
    credential_patterns = [
        (r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([a-zA-Z0-9!@#$%^&*]{4,})', 'PASSWORD'),
        (r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9]{16,})', 'API_KEY'),
        (r'(?i)(secret|token)\s*[:=]\s*["\']?([a-zA-Z0-9]{10,})', 'SECRET_TOKEN'),
        (r'(?i)(database_url|db_url|mongodb|mysql)\s*[:=]\s*["\']?([^\s"\'<>]+)', 'DATABASE_URL'),
        (r'(?i)(aws_access_key|aws_secret_key)\s*[:=]\s*["\']?([a-zA-Z0-9/+=]{20,})', 'AWS_KEY'),
    ]
    
    try:
        response = requests.get(url, timeout=5, verify=False, allow_redirects=False)
        
        for pattern, cred_type in credential_patterns:
            matches = re.finditer(pattern, response.text)
            for match in matches:
                findings.append({
                    'type': f'HARDCODED_{cred_type}',
                    'severity': 'HIGH',
                    'content': match.group(0)[:100]
                })
        
        # Check response headers for sensitive info
        if 'X-Powered-By' in response.headers:
            findings.append({
                'type': 'TECH_DISCLOSURE',
                'severity': 'LOW',
                'content': f"X-Powered-By: {response.headers['X-Powered-By']}"
            })
    except:
        pass
    
    return findings

def check_api_endpoints(host, port):
    """Scan for exposed API endpoints."""
    protocol = "https" if "443" in str(port) else "http"
    api_paths = [
        '/api', '/api/v1', '/api/v2', '/api/admin',
        '/swagger', '/swagger-ui', '/swagger-ui.html',
        '/docs', '/api/docs', '/graphql',
        '/admin', '/admin/api', '/management',
        '/actuator', '/debug', '/metrics',
        '/config', '/settings', '/backup',
    ]
    
    findings = []
    for path in api_paths:
        url = f"{protocol}://{host}:{port}{path}"
        try:
            response = requests.head(url, timeout=3, verify=False, allow_redirects=True)
            if response.status_code in [200, 301, 302, 401, 403]:
                findings.append({
                    'type': 'EXPOSED_API_ENDPOINT',
                    'severity': 'MEDIUM',
                    'content': f"Found: {path} (HTTP {response.status_code})"
                })
        except:
            pass
    
    return findings

def save_security_finding(host, port, finding_type, content, severity):
    """Save security finding to database."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO security_findings 
            (ip_address, port, finding_type, finding_content, severity, discovered_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (host, port, finding_type, content, severity, now))
        conn.commit()

def scan_target(host, port):
    """Scan a single target for security issues."""
    clean_port = str(port).split("/")[0]
    print(f"[SCANNING] {host}:{clean_port}", flush=True)
    sys.stdout.flush()
    
    findings = []
    
    # Check for .env files
    env_findings = check_env_file(host, clean_port)
    findings.extend(env_findings)
    
    # Check for hardcoded credentials
    cred_findings = check_hardcoded_credentials(host, clean_port)
    findings.extend(cred_findings)
    
    # Check for API endpoints
    api_findings = check_api_endpoints(host, clean_port)
    findings.extend(api_findings)
    
    # Save findings
    for finding in findings:
        save_security_finding(
            host, 
            clean_port, 
            finding['type'], 
            finding['content'], 
            finding['severity']
        )
        
        severity_emoji = "🔴" if finding['severity'] == 'CRITICAL' else "🟠" if finding['severity'] == 'HIGH' else "🟡"
        print(f"  {severity_emoji} {finding['type']}: {finding['content'][:60]}", flush=True)
        sys.stdout.flush()
    
    return len(findings)

def run_security_scan(num_workers=5):
    """Run security scan on all discovered assets using multithreading."""
    init_security_db()
    
    # Get all assets from database
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ip_address, port FROM web_assets")
        assets = cursor.fetchall()
    
    print(f"\n[+] Starting Security Scan on {len(assets)} targets with {num_workers} workers...")
    print("=" * 90)
    sys.stdout.flush()
    
    total_findings = 0
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(scan_target, host, port): (host, port) for host, port in assets}
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            try:
                finding_count = future.result()
                total_findings += finding_count
            except Exception as e:
                print(f"[-] Error during scan: {str(e)[:50]}", flush=True)
            
            print(f"[Progress] {completed}/{len(assets)}", flush=True)
            sys.stdout.flush()
    
    print("=" * 90)
    print(f"\n[✓] Security Scan Complete!")
    print(f"[+] Total findings: {total_findings}")
    print_security_report()

def print_security_report():
    """Print summary of security findings."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Group by severity
        cursor.execute("""
            SELECT severity, COUNT(*) FROM security_findings 
            GROUP BY severity ORDER BY severity
        """)
        
        print("\n" + "=" * 90)
        print("SECURITY FINDINGS BY SEVERITY")
        print("=" * 90)
        
        for severity, count in cursor.fetchall():
            emoji = "🔴" if severity == 'CRITICAL' else "🟠" if severity == 'HIGH' else "🟡"
            print(f"{emoji} {severity:<10}: {count} findings")
        
        # Show top findings
        cursor.execute("""
            SELECT finding_type, COUNT(*) FROM security_findings 
            GROUP BY finding_type ORDER BY COUNT(*) DESC LIMIT 10
        """)
        
        print("\n" + "-" * 90)
        print("TOP SECURITY ISSUES")
        print("-" * 90)
        
        for issue_type, count in cursor.fetchall():
            print(f"  • {issue_type}: {count} occurrences")

if __name__ == "__main__":
    run_security_scan(num_workers=8)
