import os
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "captured_screenshots"

def capture_screenshot(ip_address, port, web_title):
    """
    Opens a headless browser, navigates to the target, and snaps a picture.
    Saves the file as 'IP_PORT.png'.
    """
    # Create the output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Clean the title string to create a safe file name
    safe_title = "".join([c for c in web_title if c.isalpha() or c.isdigit() or c in ' ']).rstrip()
    safe_title = safe_title.replace(" ", "_")[:20] # Limit size
    
    # Determine the protocol based on common secure ports
    protocol = "https" if "443" in port else "http"
    
    # Clean IP formatting (strip out /tcp if present)
    clean_port = port.split("/")[0]
    url = f"{protocol}://{ip_address}:{clean_port}"
    
    filename = f"{OUTPUT_DIR}/{ip_address}_{clean_port}.png"
    
    print(f"[~] Launching headless browser for: {url}")
    
    try:
        with sync_playwright() as p:
            # Launch browser with certificates ignored (critical for internal self-signed IPs)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            
            # Set a standard screen size
            page.set_viewport_size({"width": 1280, "height": 720})
            
            # Navigate to the target with a strict 10-second timeout limit
            page.goto(url, timeout=10000, wait_until="load")
            
            # Snaps the picture
            page.screenshot(path=filename)
            browser.close()
            
            print(f"[✓] Screenshot saved successfully: {filename}")
            return filename
            
    except Exception as e:
        # Catch common connection timeouts or certificate failures gracefully
        print(f"[-] Failed to capture screenshot for {url}: Connection Timeout/Refused")
        return None
