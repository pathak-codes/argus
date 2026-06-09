import subprocess
import shutil
import re
from concurrent.futures import ThreadPoolExecutor
from database_engine import init_db, save_or_update_asset 
from screenshot_engine import capture_screenshot 


def check_nmap_installed():
    """Ensures Nmap is available on the host system path."""
    if shutil.which("nmap") is None:
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
        print("\n[!] Warning: Scanning ALL ports. Safety rate-limiting applied.")
        
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
        return
    
    init_db()
    
    hosts_data = raw_output.split("Nmap scan report for ")
    new_discoveries = 0
    total_found = 0
    screenshot_tasks = []
    
    print("=" * 90)
    print(f"{'STATUS':<8} | {'IP ADDRESS':<16} | {'PORT':<6} | {'SERVICE / VERSION':<18} | {'WEB TITLE'}")
    print("=" * 90)

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
                
                status_tag = "[NEW]" if is_new else "[KNOWN]"
                if is_new:
                    new_discoveries += 1
                
                print(f"{status_tag:<8} | {ip_address:<16} | {current_port:<6} | {current_service:<18} | {web_title}")
                screenshot_tasks.append((ip_address, current_port, web_title))
                
                current_port = ""
                current_service = ""

    print("=" * 90)
    print(f"[+] Scan Analysis Complete. Found {total_found} total web assets.")
    
    if screenshot_tasks:
        print(f"\n[~] Initializing Concurrency Engine. Processing {len(screenshot_tasks)} screenshots across 5 workers...")
        print("-" * 90)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(capture_screenshot, ip, prt, ttl) for ip, prt, ttl in screenshot_tasks]
            for future in futures:
                future.result() 
                
        print("-" * 90)
        print(f"[✓] Visual Queue Completed. Check the 'captured_screenshots/' directory.")

def run_scan(command):
    """Executes the Nmap scan and captures the raw text output."""
    print(f"\n[+] Executing: {' '.join(command)}")
    print("[+] Scan in progress... Please wait.\n")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[-] Scan failed: {e.stderr}")
        return None

if __name__ == "__main__":
    check_nmap_installed()
    
    target_ip = input("Enter target IP or range (e.g., scanme.nmap.org): ").strip()
    
    print("\nSelect Port Strategy:")
    print("1) One Specific Port")
    print("2) Multiple Specific Ports (comma-separated)")
    print("3) Web Discovery Preset (80,443,3000,5000,8080,8443,8888)")
    print("4) All Ports (1-65535) [Thorough but slower]")
    choice = input("Enter option (1-4): ").strip()
    
    custom = ""
    if choice in ["1", "2"]:
        custom = input("Enter your custom port(s): ").strip()
        
    nmap_cmd = build_nmap_command(target_ip, choice, custom)
    raw_results = run_scan(nmap_cmd)
    parse_nmap_output(raw_results)
