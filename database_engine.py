import sqlite3
from datetime import datetime

DB_NAME = "assets.db"

def init_db():
    """Creates the assets tracking table if it doesn't exist."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS web_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                port TEXT,
                service TEXT,
                web_title TEXT,
                last_seen TIMESTAMP
            )
        """)
        conn.commit()

def save_or_update_asset(ip, port, service, title):
    """
    Saves a found asset. If it already exists, updates the timestamp and info.
    Returns True if it's a brand new discovery, False if it's an update.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Check if this exact asset (IP + Port) already exists
        cursor.execute(
            "SELECT id, web_title FROM web_assets WHERE ip_address = ? AND port = ?", 
            (ip, port)
        )
        existing = cursor.fetchone()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if existing:
            asset_id, old_title = existing
            # Update existing asset tracking
            cursor.execute("""
                UPDATE web_assets 
                SET service = ?, web_title = ?, last_seen = ? 
                WHERE id = ?
            """, (service, title, now, asset_id))
            conn.commit()
            
            # Check if the website's HTML title changed
            if old_title != title:
                print(f"[!] TITLE CHANGE: {ip}:{port} changed from '{old_title}' ➔ '{title}'")
            return False
        else:
            # Insert a completely new asset
            cursor.execute("""
                INSERT INTO web_assets (ip_address, port, service, web_title, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (ip, port, service, title, now))
            conn.commit()
            return True

def get_stale_assets(current_scan_ips, network_range):
    """
    Finds assets that were previously found in this network block 
    but did NOT appear in the current scan (meaning they went offline).
    """
    # Simple check: This looks for assets not updated in the last few minutes
    # For simplicity in this stage, we can track what vanished by cross-checking lists.
    pass
