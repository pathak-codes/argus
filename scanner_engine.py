import subprocess
import shutil
import re
from database_engine import init_db, save_or_update_asset 
# Import our brand new visual capture module
from screenshot_engine import capture_screenshot 
import subprocess
import shutil
import re
import subprocess
import shutil
import re
# Import our new database controller
from database_engine import init_db, save_or_update_asset 


def check_nmap_installed():
    """Ensures Nmap is available on the host system system path."""
    if shutil.which("nmap") is None:
        raise SystemExit("Error: Nmap is not installed or not in your system PATH.")

def build_nmap_command(target, port_choice, custom_ports=""):
    """
    Dynamically builds the Nmap command based on flexible port selection.
    """
    # Core flags: Service detection (-sV), title script, and speed optimization (-T4)
    base_cmd = ["nmap", "-sV", "--script=http-title", "-T4"]
    
    # Flexible Port Logic
    if port_choice == "1":
        # Single specific port
        if not custom_ports:
            custom_ports = "80"
        base_cmd.extend(["-p", custom_ports])
        
    elif port_choice == "2":
        # Multiple specific ports (comma-separated list)
        if not custom_ports:
            custom_ports = "80,443,8080"
        base_cmd.extend(["-p", custom_ports])
        
    elif port_choice == "3":
        # Smart Web Preset (Extraordinary feature 1)
        base_cmd.extend(["-p", "80,443,3000,5000,8080,8443,8888"])
        
    elif port_choice == "4":
        # All 65,535 ports + safety rate limiting
        base_cmd.extend(["-p-", "--min-rate", "1500"])
        print("\n[!] Warning: Scanning ALL ports. Safety rate-limiting applied.")
        
    else:
        # Default to port 80 if choice is invalid
        base_cmd.extend(["-p", "80"])

    # Append the target IP range at the very end
    base_cmd.append(target)
    return base_cmd

def parse_nmap_output(raw_output):
    """
    Parses Nmap text, hides junk, prints a table, and saves/flags changes in the database.
    """
    if not raw_output:
        return
    
    # Initialize the database file/table structure
    init_db()
    
    hosts_data = raw_output.split("Nmap scan report for ")
    new_discoveries = 0
    total_found = 0
    
    print("-" * 85)
    print(f"{'STATUS':<8} | {'IP ADDRESS':<16} | {'PORT':<6} | {'SERVICE / VERSION':<18} | {'WEB TITLE'}")
    print("-" * 85)

    for host in hosts_data:
        if not host.strip():
            continue
            
        lines = host.splitlines()
        ip_match = re.match(r"^([^\s]+)", lines[0])
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
                
                # Commit to database and check if it's uniquely new
                is_new = save_or_update_asset(ip_address, current_port, current_service, web_title)
                
                # Visual Tagging: Mark brand new infrastructure with [NEW]
                status_tag = "[NEW]" if is_new else "[KNOWN]"
                if is_new:
                    new_discoveries += 1
                
                print(f"{status_tag:<8} | {ip_address:<16} | {current_port:<6} | {current_service:<18} | {web_title}")
                
                current_port = ""
                current_service = ""

    print("-" * 85)
    print(f"[+] Scan Complete. Total Active: {total_found} | New Discoveries: {new_discoveries}")


    for host in hosts_data:
        if not host.strip():
            continue
            
        # Extract the target IP address
        lines = host.splitlines()
        ip_match = re.match(r"^([^\s]+)", lines[0])
        if not ip_match:
            continue
        ip_address = ip_match.group(1)
        
        current_port = ""
        current_service = ""
        
        # Look through the host text block for open ports and script outputs
        for line in lines:
            # Match lines like: "80/tcp open  http    Apache httpd 2.4.49"
            port_match = re.search(r"^(\d+/tcp)\s+open\s+([^\s]+)\s*(.*)", line)
            if port_match:
                current_port = port_match.group(1)
                service_name = port_match.group(2)
                version_info = port_match.group(3)
                current_service = f"{service_name} ({version_info})" if version_info else service_name
                
            # Match lines like: "|_http-title: Home - Corporate Portal"
            title_match = re.search(r"\|_http-title:\s*(.*)", line)
            if title_match and current_port:
                web_title = title_match.group(1).strip()
                
                # Print clean, junk-filtered line (Extraordinary Feature 2)
                print(f"{ip_address:<18} | {current_port:<6} | {current_service:<20} | {web_title}")
                discovered_assets += 1
                
                # Reset tracking variables for the next port block
                current_port = ""
                current_service = ""

    print("-" * 75)
    print(f"[+] Extraction complete. Found {discovered_assets} active web assets.")


def run_scan(command):
    """Executes the Nmap scan and captures the raw text output."""
    print(f"\n[+] Executing: {' '.join(command)}")
    print("[+] Scan in progress... Please wait.\n")
    
    try:
        # Runs the command and waits for it to complete
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[-] Scan failed: {e.stderr}")
        return None
if __name__ == "__main__":
    check_nmap_installed()
    
    # User Input Parameters
    target_ip = input("Enter target IP or range (e.g., 51.20.0.1/22): ").strip()
    
    print("\nSelect Port Strategy:")
    print("1) One Specific Port")
    print("2) Multiple Specific Ports (comma-separated)")
    print("3) Web Discovery Preset (80,443,3000,5000,8080,8443,8888)")
    print("4) All Ports (1-65535) [Thorough but slower]")
    choice = input("Enter option (1-4): ").strip()
    
    custom = ""
    if choice in ["1", "2"]:
        custom = input("Enter your custom port(s): ").strip()
        
    # Run the core process
    nmap_cmd = build_nmap_command(target_ip, choice, custom)
    raw_results = run_scan(nmap_cmd)
    parse_nmap_output(raw_results)
