import subprocess
import shutil
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from database_engine import init_db, save_or_update_asset 
from screenshot_engine import capture_screenshot, close_all_browsers 
from banner import (
    print_argus_banner,
    print_argus_banner_compact,
    print_stage_banner,
    print_results_banner,
    print_error_banner,
    print_success_banner,
    print_pipeline_header,
    print_finding,
    ProgressSpinner,
    ScanProgressBar,
    Colors
)


def check_nmap_installed():
    """Ensures Nmap is available on the host system path."""
    if shutil.which("nmap") is None:
        print_error_banner("Nmap is not installed or not in your system PATH.")
        raise SystemExit("Error: Nmap is not installed or not in your system PATH.")

def build_nmap_command(target, port_choice, custom_ports=""):
    """
    Dynamically builds the Nmap command based on flexible port selection.
    """
    base_cmd = ["nmap", "-sV", "--script=http-title", "-T4"]
    
    if port_choice == "1":
        if not custom_ports:
            custom_ports = "80"
        base_cmd.extend(["-p", custom_ports])
        
    elif port_choice == "2":
        if not custom_ports:
            custom_ports = "80,443,8080"
        base_cmd.extend(["-p", custom_ports])
        
    elif port_choice == "3":
        base_cmd.extend(["-p", "80,443,3000,5000,8080,8443,8888"])
        
    elif port_choice == "4":
        base_cmd.extend(["-p-", "--min-rate", "1500"])
        print(f"\n{Colors.YELLOW}[!] Warning: Scanning ALL ports. Safety rate-limiting applied.{Colors.RESET}")
        
    else:
        base_cmd.extend(["-p", "80"])

    base_cmd.append(target)
    return base_cmd

def parse_nmap_output(raw_output):
    """
    Parses Nmap text, updates the tracking database, and captures 
    multiple screenshots simultaneously using a concurrent thread pool.
    """
    if not raw_output:
        print_error_banner("No scan output received")
        return
    
    init_db()
    
    print_stage_banner("discovery", 1, 4)
    print("\n")
    
    hosts_data = raw_output.split("Nmap scan report for ")
    new_discoveries = 0
    total_found = 0
    screenshot_tasks = []
    
    print_pipeline_header("Asset Discovery Results")
    print(f"\n{'STATUS':<8} | {'IP ADDRESS':<16} | {'PORT':<6} | {'SERVICE / VERSION':<18} | {'WEB TITLE'}")
    print("=" * 90)
    sys.stdout.flush()

    for host in hosts_data:
        if not host.strip():
            continue
            
        lines = host.splitlines()
        
        # Safely capture target IP identifier from text block
        ip_match = re.search(r"^([^\s]+)", host.strip())
        if not ip_match:
            continue
        ip_address = ip_match.group(1)
        
        current_port = ""
        current_service = ""
        
        for line in lines:
            port_match = re.search(r"^(\d+/tcp)\s+open\s+([^\s]+)\s*(.*)", line)
            if port_match:
                current_port = port_match.group(1)
                service_name = port_match.group(2)
                version_info = port_match.group(3)
                current_service = f"{service_name} ({version_info})" if version_info else service_name
                
            title_match = re.search(r"\|_http-title:\s*(.*)", line)
            if title_match and current_port:
                web_title = title_match.group(1).strip()
                total_found += 1
                
                is_new = save_or_update_asset(ip_address, current_port, current_service, web_title)
                
                status_tag = f"{Colors.GREEN}[NEW]{Colors.RESET}" if is_new else f"{Colors.DIM}[KNOWN]{Colors.RESET}"
                if is_new:
                    new_discoveries += 1
                
                print(f"{status_tag:<20} | {ip_address:<16} | {current_port:<6} | {current_service:<18} | {web_title}")
                sys.stdout.flush()
                screenshot_tasks.append((ip_address, current_port, web_title))
                
                current_port = ""
                current_service = ""

    print("=" * 90)
    print(f"\n{Colors.GREEN}[+]{Colors.RESET} Scan Analysis Complete. Found {Colors.BOLD}{total_found}{Colors.RESET} total web assets ({Colors.GREEN}{new_discoveries} NEW{Colors.RESET})")
    sys.stdout.flush()
    
    if screenshot_tasks:
        print_stage_banner("discovery", 1, 4)
        print(f"\n{Colors.CYAN}[~] Processing {len(screenshot_tasks)} screenshots across 4 workers...{Colors.RESET}")
        print(f"{Colors.CYAN}[~] Each worker thread starts its own browser instance.{Colors.RESET}")
        print("-" * 90)
        sys.stdout.flush()

        # Progress bar for screenshot capture
        progress_bar = ScanProgressBar(len(screenshot_tasks), prefix="Screenshot Capture")
        
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(capture_screenshot, ip, prt, ttl) for ip, prt, ttl in screenshot_tasks]
                completed = 0
                for future in futures:
                    try:
                        future.result()
                        progress_bar.update(1)
                    except Exception as e:
                        progress_bar.update(1)
                        sys.stdout.flush()

            progress_bar.close("Screenshots captured successfully")
            print("-" * 90)
            print(f"\n{Colors.SUCCESS}[✓]{Colors.RESET} Visual Capture Complete. Check the '{Colors.BOLD}captured_screenshots/{Colors.RESET}' directory.")
            sys.stdout.flush()
        except Exception as e:
            print_error_banner(f"Screenshot capture failed: {str(e)}")
        finally:
            close_all_browsers()

def run_scan(command):
    """Executes the Nmap scan with REAL-TIME output streaming."""
    print(f"\n{Colors.GREEN}[+]{Colors.RESET} Executing: {Colors.BOLD}{' '.join(command)}{Colors.RESET}")
    print(f"{Colors.GREEN}[+]{Colors.RESET} Streaming output live:\n")
    print("-" * 90)
    sys.stdout.flush()
    
    scan_start = time.time()
    
    try:
        # Stream output line-by-line as nmap produces it (not buffered)
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # Line buffered for real-time output
        )
        
        output_lines = []
        
        # Read and print output in real-time
        for line in process.stdout:
            line = line.rstrip('\n')
            print(line)
            sys.stdout.flush()
            output_lines.append(line)
        
        process.wait(timeout=600)  # Wait up to 10 minutes
        
        if process.returncode != 0:
            print(f"\n{Colors.YELLOW}[-]{Colors.RESET} Scan completed with warnings (exit code {process.returncode})")
        
        print("-" * 90)
        scan_duration = time.time() - scan_start
        print(f"{Colors.SUCCESS}[✓]{Colors.RESET} Nmap scan completed in {Colors.BOLD}{scan_duration:.2f}s{Colors.RESET}")
        return "\n".join(output_lines), scan_duration
        
    except subprocess.TimeoutExpired:
        process.kill()
        print(f"\n{Colors.CRITICAL}[-]{Colors.RESET} Scan timeout after 10 minutes")
        sys.stdout.flush()
        return None, 0
        
    except Exception as e:
        print(f"\n{Colors.CRITICAL}[-]{Colors.RESET} Scan error: {str(e)}")
        sys.stdout.flush()
        return None, 0

if __name__ == "__main__":
    # Display main banner
    print_argus_banner()
    time.sleep(1)
    
    # Verify Nmap installation
    try:
        check_nmap_installed()
    except SystemExit:
        sys.exit(1)
    
    print("\n")
    target_ip = input(f"{Colors.CYAN}[?]{Colors.RESET} Enter target IP or range (e.g., scanme.nmap.org): ").strip()
    
    if not target_ip:
        print_error_banner("No target provided")
        sys.exit(1)
    
    print(f"\n{Colors.BOLD}Select Port Strategy:{Colors.RESET}")
    print("  1) One Specific Port")
    print("  2) Multiple Specific Ports (comma-separated)")
    print("  3) Web Discovery Preset (80,443,3000,5000,8080,8443,8888)")
    print("  4) All Ports (1-65535) [Thorough but slower]")
    choice = input(f"{Colors.CYAN}[?]{Colors.RESET} Enter option (1-4): ").strip()
    
    custom = ""
    if choice in ["1", "2"]:
        custom = input(f"{Colors.CYAN}[?]{Colors.RESET} Enter your custom port(s): ").strip()
        
    nmap_cmd = build_nmap_command(target_ip, choice, custom)
    
    # Stage 1: Asset Discovery
    print_stage_banner("discovery", 1, 4)
    print("\n")
    
    result = run_scan(nmap_cmd)
    if result:
        raw_results, scan_duration = result
        parse_nmap_output(raw_results)
        
        # Show completion banner
        print_success_banner(f"Asset discovery completed for {target_ip}")
    else:
        print_error_banner("Scan failed or was interrupted")
        sys.exit(1)
