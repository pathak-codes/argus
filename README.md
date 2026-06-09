# ⚡ HTTP-Vision-Nmap

An automated, hyper-fast asset discovery engine that pairs `nmap` banner grabbing with headless browser automation. Built to kill the noise of massive subnet scanning and deliver instant visual intelligence.

---

## 🚀 Core Capabilities

* **Junk-Filtered Output**: Strips away dead hosts and closed ports automatically.
* **Stateful Delta-Tracking**: Micro-DB persistence flags infra changes (`[NEW]` vs `[KNOWN]`).
* **Asynchronous Capture**: Headless Playwright pool snaps visuals concurrently.
* **Smart Rate-Limiting**: Safety throttles applied automatically on wide-scope scans.

---

## 🛠️ System Architecture

```text
my-nmap-scanner/
├── scanner_engine.py       # Main Entrypoint & Text Mining Parser
├── database_engine.py      # SQLite Asset State Engine
├── screenshot_engine.py    # Multi-Threaded Headless Browser Workers
└── assets.db               # Local State Persistence (Auto-Generated)
```

---

## ⚡ Quickstart

### 1. Prerequisites
Ensure you have `nmap` installed on your system path.

```bash
# macOS
brew install nmap

# Ubuntu/Debian
sudo apt install nmap
```

### 2. Install Project Dependencies
```bash
pip install playwright
playwright install chromium
```

### 3. Spin It Up
```bash
python scanner_engine.py
```

---

## 📊 Presets & Execution Logic

| Preset | Target Scope | Added Flags | Best For |
| :--- | :--- | :--- | :--- |
| **`1`** | Single Custom Port | `-p <port>` | Targeted checks |
| **`2`** | Multi Custom Ports | `-p <ports>` | Specific service audits |
| **`3`** | Web Discovery Preset | `-p 80,443,3000...` | Attack surface mapping |
| **`4`** | All-Ports Execution | `-p- --min-rate 1500` | Full perimeter validation |

---

## 📄 Output Visualization Blueprint

```text
==========================================================================================
STATUS   | IP ADDRESS       | PORT   | SERVICE / VERSION    | WEB TITLE
==========================================================================================
[NEW]    | 51.20.0.45       | 80/tcp | http (Apache 2.4)    | Corporate Login
[~] Launching headless browser for: http://51.20.0.45:80
[✓] Screenshot saved successfully: captured_screenshots/51.20.0.45_80.png
------------------------------------------------------------------------------------------
[KNOWN]  | 51.20.0.99       | 443/tcp| https (nginx)        | Staging Environment
==========================================================================================
[+] Scan Analysis Complete. Found 2 total web assets.
```

---

## 🛡️ Operational Guardrails

* **Rate Warning**: Scanning all 65k ports on massive scopes (like a `/22`) will create network noise. Use Preset `3` for broad coverage without triggering firewalls.
* **Self-Signed Certificates**: The browser core ignores TLS/SSL errors natively. It will snap admin panels even if their certs are broken.

---

## 🤝 Contributing
* Fork it.
* Push your feature branch.
* Ensure code passes structural verification.
