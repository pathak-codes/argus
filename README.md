# 🕵️ ARGUS — Advanced Reconnaissance & Governance Unified System

Automated network asset discovery, HTTP intelligence, vulnerability scanning, and content triage — built for pentesters and SOC teams who need signal, not noise.

Python 3.11+ | License: MIT

---

## Why ARGUS Exists

Nmap gives you raw port scans. Curl gives you HTTP status codes. Neither tells you what matters.

ARGUS bridges that gap. It's a unified reconnaissance pipeline that takes a raw subnet range and produces one answer:

> What web services are running on this network, which ones are vulnerable, and which ones are worth investigating further?

---

## Real-World Use Cases

| Who Uses It | What They Get |
|-------------|---------------|
| Pentesters | Subnet-wide asset discovery with visual proof — screenshots of every live web service |
| SOC Analysts | Automated delta tracking — `[NEW]` vs `[KNOWN]` flags infrastructure drift |
| Security Engineers | Multi-method HTTP analysis — detect 403 resource existence, 401 auth schemes, redirect chains |
| Red Teams | Security vulnerability sweep — `.env` exposures, hardcoded credentials, exposed Swagger/GraphQL |
| Incident Responders | Prioritized endpoint list — `--interesting-only` filters to HIGH severity findings |

---

## What It Actually Produces

ARGUS doesn't just "run nmap" — it generates actionable artifacts at every stage:

```
📊 Asset Discovery Table
├── Host: ec2-51-20-0-62.eu-north-1.compute.amazonaws.com
│   ├── Port: 80/tcp
│   ├── Service: http (nginx 1.22.0)
│   ├── Title: "dKey Service API"
│   └── Status: [NEW] — first time seen

🔍 HTTP Analysis Report (JSON)
├── Target: 51.20.0.0/22
├── Priority Distribution: 42 HIGH, 18 MEDIUM, 36 LOW
├── Interesting Situations:
│   ├── Multi-status endpoint: GET=403, OPTIONS=200, TRACE=405
│   ├── Large 500 body: 48KB (possible stack trace)
│   └── Redirect chain: 5 hops → / → /en → /login → /auth → /dashboard

🔐 Security Scan Results
├── 8 CRITICAL: Exposed .env files with database credentials
├── 15 HIGH: Hardcoded API keys (sk_live_*, aws_secret_key)
├── 22 MEDIUM: Unauthenticated API endpoints (/graphql, /actuator)
└── 18 LOW: Tech stack disclosure (X-Powered-By, Server headers)

🖼️ Content Triage Output
├── results/screenshots/    # Only meaningful pages (score >= 3)
├── results/metadata/       # Per-screenshot JSON with title, server, status
└── results/reports/        # summary.json with duration, dedup stats
```

---

## Skills & Technologies Demonstrated

This project demonstrates practical intersections between security engineering and systems architecture:

- **Network Scanning & OSINT**: Nmap automation with real-time subprocess streaming, service version detection, regex-based output parsing
- **Systems Architecture**: Stateful SQLite persistence with delta tracking (`[NEW]` vs `[KNOWN]`), thread-safe singleton browser management
- **Concurrent Programming**: ThreadPoolExecutor with thread-local Playwright instances, producer-consumer task queues, LRU dedup caches
- **Browser Automation**: Headless Chromium screenshot pipeline with configurable viewport, timeout, and TLS bypass for self-signed certs
- **Vulnerability Detection**: Multi-pattern credential regex engine, `.env` exposure scanning, API endpoint enumeration against 15+ common paths
- **Content Intelligence**: Heuristic page scoring engine (+3 title, +2 login keywords, +2 admin keywords, +1 forms, +1 JavaScript) with configurable thresholds
- **Data Serialization**: Structured JSON export with priority/status distributions, metadata per finding

---

## Architecture

ARGUS is a multi-stage unidirectional pipeline — each stage has explicit inputs, isolated execution, and produces structured artifacts consumed by the next stage.

```
                            COLLECTION
                                │
                    ┌───────────▼───────────────┐
                    │   scanner_engine.py       │
                    │   • Nmap subprocess       │
                    │   • Real-time streaming   │
                    │   • Regex output parsing  │
                    └───────────┬───────────────┘
                                │ assets.db
                                ▼
                    ┌───────────────────────────┐
                    │   screenshot_engine.py     │
                    │   • Thread-local browsers  │
                    │   • 4-worker pool          │
                    │   • captured_screenshots/  │
                    └───────────────────────────┘
                                │
                    ┌───────────▼───────────────┐
                    │   http_analyzer.py         │
                    │   • 7-method probing       │
                    │   • Priority classification│
                    │   • Interesting detection  │
                    └───────────┬───────────────┘
                                │
                    ┌───────────▼───────────────┐
                    │   security_scanner.py     │
                    │   • .env / credential scan│
                    │   • API endpoint enum     │
                    │   • 8-worker pool         │
                    └───────────┬───────────────┘
                                │
                    ┌───────────▼───────────────┐
                    │   triage/ pipeline         │
                    │   • HTTP analysis          │
                    │   • Content scoring        │
                    │   • Screenshot filtering   │
                    │   • results/{screenshots,  │
                    │     metadata, reports}/    │
                    └───────────────────────────┘
```

---

## Key Design Decisions

- **Thread-local browsers** — Playwright's sync API uses greenlets tied to their creating thread. Sharing a browser across threads crashes. Each worker spawns its own Chromium instance via `threading.local()`.
- **Unidirectional data flow** — Raw → Normalized → Enriched → Scored. No stage mutates upstream data. Each stage can be re-run independently.
- **Fail-soft architecture** — Individual target timeouts never block the pipeline. Thread pools use `as_completed` with per-future exception handling.
- **Evidence-based scoring** — Every triage score is decomposable: +3 for title, +2 for login keywords, +2 for admin keywords, +1 for forms, +1 for JS. You can trace exactly why a page scored 7/10.
- **Priority over noise** — Default output hides 404s and LOW findings. `--interesting-only` further filters to HIGH only. `--show-all` is explicit opt-in.

---

## Project Structure

```
ARGUS/
│
├── scanner_engine.py           # Nmap subprocess orchestrator, real-time streaming, regex parsing
├── database_engine.py          # SQLite delta-tracking engine — [NEW] vs [KNOWN]
├── screenshot_engine.py        # Thread-local Playwright browser pool — 4 workers
│
├── http_analyzer.py            # Multi-method HTTP probing (GET/HEAD/OPTIONS/POST/PUT/DELETE/PATCH/TRACE)
├── status_classifier.py        # Priority categorization (HIGH/MEDIUM/LOW)
├── output_formatter.py         # Table display with priority filtering + summary
├── json_exporter.py            # Full finding serialization to JSON
│
├── security_scanner.py         # .env detection, credential regex, API endpoint enumeration
├── run_security_scan.py        # Security scanner CLI launcher
├── run_http_analysis.py        # HTTP analyzer CLI with argparse flags
│
├── triage/                     # Content triage subsystem (8 classes)
│   ├── scan_manager.py         # Pipeline orchestrator
│   ├── target_queue.py         # Priority queue + LRU dedup cache
│   ├── http_analyzer.py        # Connection-pooled HTTP analysis
│   ├── content_classifier.py   # Scoring engine + error/default page detection
│   ├── screenshot_manager.py   # Thread-local shared browser capture
│   ├── storage_manager.py      # Dedup + results/{screenshots,metadata,reports}/logs/
│   └── report_generator.py     # summary.json with metrics
│
├── run_triage.py               # Content triage CLI entry point
│
├── assets.db                   # SQLite database (auto-generated)
├── captured_screenshots/       # Scanner screenshots (auto-generated)
├── results/                    # Triage output (auto-generated)
│
├── README.md
├── PROJECT_REPORT.md           # Full technical documentation
└── overview.txt                # Nmap reference notes
```

---

## Quick Start

### Prerequisites

```bash
# Nmap 7.99+
nmap --version

# Python 3.11+
python --version
```

### Installation

```bash
git clone <your-repo-url> ARGUS
cd ARGUS

python -m venv .venv
source .venv/bin/activate     # Linux/macOS
# .\.venv\Scripts\Activate.ps1  # Windows

pip install playwright requests
python -m playwright install chromium
```

---

## Usage

### 1 — Asset Discovery

```bash
python scanner_engine.py
```

Interactive prompts for target IP/range and port strategy:

| Preset | Ports | Best For |
|--------|-------|----------|
| 1 | Single custom | Targeted checks |
| 2 | Multiple custom | Specific service audits |
| 3 | 80,443,3000,5000,8080,8443,8888 | Web attack surface mapping |
| 4 | All 1-65535 (rate-limited) | Full perimeter validation |

Output: `assets.db` + `captured_screenshots/*.png`

### 2 — HTTP Status Analysis

```bash
python run_http_analysis.py
```

| Flag | Effect |
|------|--------|
| `-i` / `--interesting-only` | HIGH priority only |
| *(default)* | HIGH + MEDIUM |
| `-a` / `--show-all` | Every status including 404 |
| `-j -o report.json` | JSON export |
| `-w 20` | 20 concurrent workers |
| `-t 8` | 8-second timeout |

Probes 7 methods per endpoint, detects multi-status endpoints, redirect chains >3 hops, 401 auth schemes, large 500 bodies.

### 3 — Security Vulnerability Scan

```bash
python run_security_scan.py
```

| Severity | What It Finds |
|----------|---------------|
| 🔴 CRITICAL | Exposed `.env` / `.env.local` / `.env.example` files |
| 🟠 HIGH | Hardcoded passwords, API keys (`sk-*`), AWS secret keys |
| 🟡 MEDIUM | Unauthenticated Swagger, GraphQL, admin panels, actuators |
| ⚪ LOW | Tech stack disclosure (X-Powered-By, Server headers) |

### 4 — Content Triage

```bash
python run_triage.py
```

Intelligently filters and scores pages before screenshotting:

| Signal | Points |
|--------|--------|
| Title present | +3 |
| Content > 5 KB | +2 |
| Login keywords | +2 |
| Admin keywords | +2 |
| Form elements | +1 |
| JavaScript | +1 |
| Credential patterns | +1 |
| Body > 50 KB | +1 |

Default threshold: 3. Screenshots only for pages scoring >= threshold.

| Flag | Default | Effect |
|------|---------|--------|
| `--http-workers` | 10 | Parallel HTTP workers |
| `--min-score` | 3 | Minimum content score |
| `--min-length` | 1024 | Minimum content bytes |
| `-o results/` | results/ | Output directory |

---

## How the Triage Scoring Works

Every page accumulates evidence from the HTTP response. The Content Classifier converts this into a single score:

```
Score = Σ(signal_value)

Example: dKey Service API page
  +3  Title: "dKey Service API"
  +2  Content: 89 KB > 5 KB
  +2  Admin keywords: "Service" + "API"
  +1  Form element detected
  +1  JavaScript detected (script src)
  = 9  → Screenshot captured (threshold: 3)

Example: 404 Not Found page
  +3  Title: "404 Not Found"
  = 3  → Filtered (KNOWN_ERROR_PATTERN match overrides score)
```

---

## Testing

```bash
# Syntax check all modules
python -c "import py_compile; [py_compile.compile(f, doraise=True) for f in ...]"

# Integration test (requires live targets)
python -c "
from http_analyzer import HttpAnalyzer
from content_classifier import ContentClassifier
a = HttpAnalyzer(timeout=3)
result = a.analyze('scanme.nmap.org', '80')
c = ContentClassifier()
print(f'Status: {result.status}, Score: {c.score(result)}, Screenshot: {c.should_screenshot(result)}')
"
```

---

## Security & OpSec

- ✅ All HTTP requests route through a connection-pooled `requests.Session` with retry backoff
- ✅ SSL certificate verification disabled for self-signed internal certificates
- ✅ No clearnet fallback for error handling — timeouts halt cleanly
- ✅ Thread-local Playwright instances prevent greenlet cross-thread contamination
- ✅ Screenshot deduplication via `{title}::{status}::{content_length}` hash — no redundant captures
- ✅ Configurable worker counts prevent network congestion on large subnets
- ✅ Only scanned data stored locally — no telemetry, no external callbacks

---

## Legal

For authorized security testing only.

Unauthorized network scanning may violate the Computer Fraud and Abuse Act (CFAA) and equivalent laws in other jurisdictions. You are responsible for ensuring compliance with all applicable laws before using this tool.

---

## Contributing

Contributions welcome. Rules:

- All Tor? No — this project scans clearnet. Keep it there.
- New analyzers must emit structured finding dicts with explicit severity
- Screenshot pipeline changes must preserve thread-local browser isolation
- Tests required for new logic — run `pytest` before submitting
- Maintain unidirectional data flow: raw → processed → reported (no back-mutation)
