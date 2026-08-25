"""
ARGUS Banner & Progress Display System
Advanced Reconnaissance & Governance Unified System

Provides:
  - Professional ASCII banners with color support
  - Stage progress indicators
  - Results summary displays
  - Spinner animations for long-running tasks
"""

import sys
import time
from typing import Dict, Optional
from itertools import cycle

# Color codes for terminal output
class Colors:
    """ANSI terminal color codes"""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    DIM = '\033[2m'
    
    # Severity colors
    CRITICAL = RED
    HIGH = '\033[38;5;208m'  # Orange
    MEDIUM = YELLOW
    LOW = '\033[38;5;246m'   # Gray
    INFO = CYAN
    SUCCESS = GREEN


class Spinners:
    """Collection of spinner animations"""
    DOTS = cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    BLOCKS = cycle(['▏', '▎', '▍', '▌', '▋', '▊', '▉'])
    ARROWS = cycle(['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'])
    PULSE = cycle(['◐', '◓', '◑', '◒'])
    CYBER = cycle(['⡿', '⣟', '⣯', '⣷', '⣾', '⣽', '⣻', '⢿'])


def print_argus_banner(color: bool = True) -> None:
    """
    Print the main ARGUS banner with optional ANSI colors.
    
    Args:
        color: Enable terminal colors (default: True)
    """
    c = Colors if color else type('DummyColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('_')})()
    
    banner = f"""{c.CYAN}
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║                    {c.BOLD}█████╗ ██████╗  ██████╗ ██╗   ██╗███████╗{c.CYAN}    ║
    ║                    {c.BOLD}██╔══██╗██╔══██╗██╔════╝ ██║   ██║██╔════╝{c.CYAN}    ║
    ║                    {c.BOLD}███████║██████╔╝██║  ███╗██║   ██║███████╗{c.CYAN}    ║
    ║                    {c.BOLD}██╔══██║██╔══██╗██║   ██║██║   ██║╚════██║{c.CYAN}    ║
    ║                    {c.BOLD}██║  ██║██║  ██║╚██████╔╝╚██████╔╝███████║{c.CYAN}    ║
    ║                    {c.BOLD}╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝{c.CYAN}    ║
    ║                                                                           ║
    ║{c.BOLD}          [ ADVANCED RECONNAISSANCE & GOVERNANCE UNIFIED SYSTEM ]{c.CYAN}     ║
    ║                                                                           ║
    ║  {c.GREEN}Stateful Network Discovery Engine{c.CYAN} | {c.GREEN}Nmap Automation{c.CYAN} | {c.GREEN}Headless Scraping{c.CYAN}  ║
    ║  {c.GREEN}HTTP Intelligence{c.CYAN} | {c.GREEN}Credential Detection{c.CYAN} | {c.GREEN}Content Triage{c.CYAN}          ║
    ║                                                                           ║
    ║  {c.WHITE}Author    :{c.CYAN} Rudraksh Yadav                                              ║
    ║  {c.WHITE}Framework :{c.CYAN} Python 3.11+ | Playwright | SQLite | ThreadPoolExecutor     ║
    ║  {c.WHITE}Architecture :{c.CYAN} Multi-stage Unidirectional Pipeline                       ║
    ║  {c.WHITE}License   :{c.CYAN} MIT                                                          ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝{c.RESET}
    """
    print(banner)


def print_argus_banner_compact(color: bool = True) -> None:
    """Print compact version of ARGUS banner."""
    c = Colors if color else type('DummyColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('_')})()
    
    banner = f"""{c.CYAN}
    ┌─────────────────────────────────────────────────────────────┐
    │  {c.BOLD}🕵️  ARGUS{c.CYAN} — Advanced Reconnaissance & Governance System   │
    │                                                             │
    │  {c.GREEN}Network Discovery{c.CYAN} → {c.GREEN}HTTP Analysis{c.CYAN} → {c.GREEN}Security Scanning{c.CYAN}      │
    │  {c.GREEN}Vulnerability Assessment{c.CYAN} → {c.GREEN}Content Triage{c.CYAN}                  │
    └─────────────────────────────────────────────────────────────┘{c.RESET}
    """
    print(banner)


def print_stage_banner(stage_name: str, stage_number: int, total_stages: int = 4, color: bool = True) -> None:
    """
    Print banner for each pipeline stage.
    
    Args:
        stage_name: Name of the stage (discovery, analysis, security, triage)
        stage_number: Current stage number
        total_stages: Total number of stages
        color: Enable colors
    """
    c = Colors if color else type('DummyColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('_')})()
    
    stages = {
        "discovery": f"{c.CYAN}🔍 ASSET DISCOVERY{c.RESET}",
        "analysis": f"{c.BLUE}📊 HTTP ANALYSIS{c.RESET}",
        "security": f"{c.RED}🔐 SECURITY SCANNING{c.RESET}",
        "triage": f"{c.YELLOW}📋 CONTENT TRIAGE{c.RESET}"
    }
    
    title = stages.get(stage_name.lower(), f"{c.BOLD}{stage_name.upper()}{c.RESET}")
    progress = f"[{stage_number}/{total_stages}]"
    
    # Progress bar
    filled = int((stage_number / total_stages) * 20)
    bar = f"{c.GREEN}{'█' * filled}{c.DIM}{'░' * (20 - filled)}{c.RESET}"
    
    stage_banner = f"""
    {c.CYAN}┌──────────────────────────────────────────────────────────────┐
    │  {title:<60}{c.CYAN}│
    │  {bar:<60}{c.CYAN}│
    │  Progress: {progress:<50}{c.CYAN}│
    └──────────────────────────────────────────────────────────────┘{c.RESET}
    """
    print(stage_banner)


def print_results_banner(target: str, findings: Dict, duration: float = 0, color: bool = True) -> None:
    """
    Print results summary banner with severity breakdown.
    
    Args:
        target: Target IP/range
        findings: Dict with keys: critical, high, medium, low, screenshots, interesting
        duration: Execution time in seconds
        color: Enable colors
    """
    c = Colors if color else type('DummyColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('_')})()
    
    critical = findings.get('critical', 0)
    high = findings.get('high', 0)
    medium = findings.get('medium', 0)
    low = findings.get('low', 0)
    screenshots = findings.get('screenshots', 0)
    interesting = findings.get('interesting', 0)
    
    duration_str = f"{duration:.2f}s" if duration > 0 else "N/A"
    
    # Build severity lines with colors
    crit_line = f"{c.CRITICAL}🔴 CRITICAL{c.RESET}    : {critical:<38}"
    high_line = f"{c.HIGH}🟠 HIGH{c.RESET}        : {high:<38}"
    med_line = f"{c.MEDIUM}🟡 MEDIUM{c.RESET}      : {medium:<38}"
    low_line = f"{c.LOW}⚪ LOW{c.RESET}         : {low:<38}"
    
    results = f"""{c.CYAN}
    ╔═════════════════════════════════════════════════════════════╗
    ║  {c.BOLD}📄 RECONNAISSANCE REPORT{c.CYAN} — {target:<35}║
    ╠═════════════════════════════════════════════════════════════╣
    ║  {crit_line}{c.CYAN}║
    ║  {high_line}{c.CYAN}║
    ║  {med_line}{c.CYAN}║
    ║  {low_line}{c.CYAN}║
    ╠═════════════════════════════════════════════════════════════╣
    ║  {c.GREEN}📸 Screenshots Captured{c.CYAN}  : {screenshots:<35}║
    ║  {c.GREEN}🎯 Interesting Findings{c.CYAN}  : {interesting:<35}║
    ║  {c.GREEN}⏱️  Execution Time{c.CYAN}        : {duration_str:<35}║
    ╚═════════════════════════════════════════════════════════════╝{c.RESET}
    """
    print(results)


def print_error_banner(error_msg: str, color: bool = True) -> None:
    """Print error banner."""
    c = Colors if color else type('DummyColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('_')})()
    
    error = f"""{c.CRITICAL}
    ╔═════════════════════════════════════════════════════════════╗
    ║  {c.BOLD}❌ ERROR{c.CRITICAL}                                                ║
    ╠═════════════════════════════════════════════════════════════╣
    ║  {error_msg:<59}{c.CRITICAL}║
    ╚═════════════════════════════════════════════════════════════╝{c.RESET}
    """
    print(error)


def print_success_banner(msg: str, color: bool = True) -> None:
    """Print success banner."""
    c = Colors if color else type('DummyColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('_')})()
    
    success = f"""{c.SUCCESS}
    ╔═════════════════════════════════════════════════════════════╗
    ║  {c.BOLD}✓ SUCCESS{c.SUCCESS}                                               ║
    ╠═════════════════════════════════════════════════════════════╣
    ║  {msg:<59}{c.SUCCESS}║
    ╚═════════════════════════════════════════════════════════════╝{c.RESET}
    """
    print(success)


class ProgressSpinner:
    """Reusable spinner for long-running tasks."""
    
    def __init__(self, message: str = "Processing", spinner_type: str = "dots", color: bool = True):
        """
        Initialize progress spinner.
        
        Args:
            message: Status message to display
            spinner_type: Type of spinner (dots, blocks, arrows, pulse, cyber)
            color: Enable colors
        """
        self.message = message
        self.spinner_type = spinner_type
        self.color = color
        self.c = Colors if color else type('DummyColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('_')})()
        
        # Select spinner
        spinners_map = {
            'dots': Spinners.DOTS,
            'blocks': Spinners.BLOCKS,
            'arrows': Spinners.ARROWS,
            'pulse': Spinners.PULSE,
            'cyber': Spinners.CYBER
        }
        self.spinner = spinners_map.get(spinner_type, Spinners.DOTS)
        self.running = False
    
    def start(self) -> None:
        """Start the spinner."""
        self.running = True
        self._spin()
    
    def stop(self, final_message: Optional[str] = None) -> None:
        """Stop the spinner."""
        self.running = False
        if final_message:
            print(f"\r{self.c.GREEN}✓{self.c.RESET} {final_message:<50}", end='\n')
        else:
            print(f"\r{self.c.GREEN}✓{self.c.RESET} {self.message:<50}", end='\n')
        sys.stdout.flush()
    
    def _spin(self) -> None:
        """Internal spin animation loop."""
        while self.running:
            print(f"\r{self.c.CYAN}{next(self.spinner)}{self.c.RESET} {self.message:<50}", end='', flush=True)
            time.sleep(0.1)


class ScanProgressBar:
    """Progress bar for scan operations."""
    
    def __init__(self, total: int, prefix: str = "", color: bool = True):
        """
        Initialize progress bar.
        
        Args:
            total: Total items to process
            prefix: Prefix message
            color: Enable colors
        """
        self.total = total
        self.current = 0
        self.prefix = prefix
        self.color = color
        self.c = Colors if color else type('DummyColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('_')})()
        self.start_time = time.time()
    
    def update(self, increment: int = 1) -> None:
        """Update progress bar."""
        self.current += increment
        self._render()
    
    def _render(self) -> None:
        """Render the progress bar."""
        if self.total == 0:
            return
        
        percent = self.current / self.total
        filled = int(40 * percent)
        bar = f"{self.c.GREEN}{'█' * filled}{self.c.DIM}{'░' * (40 - filled)}{self.c.RESET}"
        
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f"{eta:.0f}s"
        else:
            eta_str = "N/A"
        
        status = f"{self.c.CYAN}{self.prefix}{self.c.RESET} {bar} {percent*100:5.1f}% [{self.current}/{self.total}] ETA: {eta_str}"
        print(f"\r{status}", end='', flush=True)
    
    def close(self, final_msg: Optional[str] = None) -> None:
        """Close and finish the progress bar."""
        total_time = time.time() - self.start_time
        print()
        if final_msg:
            print(f"{self.c.SUCCESS}✓{self.c.RESET} {final_msg} ({total_time:.2f}s)")
        else:
            print(f"{self.c.SUCCESS}✓{self.c.RESET} Complete in {total_time:.2f}s")


def print_pipeline_header(stage: str, color: bool = True) -> None:
    """Print a formatted pipeline stage header."""
    c = Colors if color else type('DummyColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('_')})()
    
    header = f"{c.CYAN}{'='*80}{c.RESET}\n"
    header += f"{c.BOLD}{c.CYAN}[*] {stage}{c.RESET}\n"
    header += f"{c.CYAN}{'='*80}{c.RESET}"
    print(header)


def print_finding(severity: str, title: str, details: str = "", color: bool = True) -> None:
    """Print a formatted security finding."""
    c = Colors if color else type('DummyColors', (), {attr: '' for attr in dir(Colors) if not attr.startswith('_')})()
    
    severity_colors = {
        'CRITICAL': c.CRITICAL + '🔴',
        'HIGH': c.HIGH + '🟠',
        'MEDIUM': c.MEDIUM + '🟡',
        'LOW': c.LOW + '⚪'
    }
    
    severity_str = severity_colors.get(severity, c.WHITE + '•')
    
    finding = f"\n{severity_str}{c.RESET} {c.BOLD}{title}{c.RESET}"
    if details:
        finding += f"\n   {c.DIM}{details}{c.RESET}"
    
    print(finding)


if __name__ == "__main__":
    # Demo all banner types
    print_argus_banner()
    print("\n")
    
    time.sleep(1)
    print_argus_banner_compact()
    print("\n")
    
    time.sleep(1)
    for i in range(1, 5):
        stage_names = ["discovery", "analysis", "security", "triage"]
        print_stage_banner(stage_names[i-1], i, 4)
        time.sleep(0.5)
    print("\n")
    
    time.sleep(1)
    print_results_banner("192.168.1.0/24", {
        "critical": 8,
        "high": 15,
        "medium": 22,
        "low": 18,
        "screenshots": 42,
        "interesting": 19
    }, duration=247.34)
    print("\n")
    
    time.sleep(1)
    print_success_banner("Scan completed successfully!")
    print("\n")
    
    time.sleep(1)
    print_error_banner("Nmap process timed out after 10 minutes")
    print("\n")
    
    # Demo spinner
    spinner = ProgressSpinner("Capturing screenshots", spinner_type="cyber")
    print("Demo: Starting spinner...")
    for i in range(30):
        time.sleep(0.1)
    spinner.running = False
    print(f"\r{Colors.GREEN}✓{Colors.RESET} Spinner demo complete!{' '*40}")
    print("\n")
    
    # Demo progress bar
    print("Demo: Progress bar...")
    bar = ScanProgressBar(100, prefix="Scanning ports")
    for i in range(100):
        time.sleep(0.05)
        bar.update()
    bar.close("Scan finished")
    print("\n")
    
    # Demo finding
    print_finding("CRITICAL", "Exposed .env File", "Found sensitive credentials in /app/.env")
    print_finding("HIGH", "Hardcoded API Key", "AWS secret key detected in config.py:42")
    print_finding("MEDIUM", "Unauthenticated API", "/graphql endpoint accessible without auth")
