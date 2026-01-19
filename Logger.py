import subprocess
import json
import csv
import os
import platform
from datetime import datetime

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_OS = platform.system()

# Set path to the Speedtest engine based on the OS
if SYSTEM_OS == "Windows":
    # On Lenovo: Looks for speedtest.exe in the same folder as this script
    SPEEDTEST_CMD = os.path.join(SCRIPT_DIR, "speedtest.exe")
else:
    # On Mac: Uses the 'speedtest' command installed via Brew
    SPEEDTEST_CMD = "speedtest"

# Local CSV file path
LOG_FILE = os.path.join(SCRIPT_DIR, "office_internet_speeds.csv")
# ---------------------

def run_test():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Launching Speedtest on {SYSTEM_OS}...")
    
    # Check if Windows binary exists before starting
    if SYSTEM_OS == "Windows" and not os.path.exists(SPEEDTEST_CMD):
        print(f"ERROR: 'speedtest.exe' not found in {SCRIPT_DIR}")
        return

    try:
        # Run Ookla CLI with JSON formatting
        cmd = [SPEEDTEST_CMD, '-f', 'json', '--accept-license']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Speedtest Error: {result.stderr}")
            return

        # Parse raw JSON data
        data = json.loads(result.stdout)
        
        # Calculations (Convert Bytes to Mbps)
        download_mbps = round(data['download']['bandwidth'] / 125000, 2)
        upload_mbps = round(data['upload']['bandwidth'] / 125000, 2)
        
        # 1. VISUAL TERMINAL OUTPUT
        print("="*40)
        print(f"ISP:      {data['isp']}")
        print(f"SERVER:   {data['server']['name']} ({data['server']['location']})")
        print(f"PING:     {data['ping']['latency']} ms")
        print(f"JITTER:   {data['ping']['jitter']} ms")
        print(f"DOWNLOAD: {download_mbps} Mbps")
        print(f"UPLOAD:   {upload_mbps} Mbps")
        print(f"URL:      {data['result']['url']}")
        print("="*40)

        # 2. PREPARE DATA FOR CSV
        row = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Device": platform.node(),
            "Download_Mbps": download_mbps,
            "Upload_Mbps": upload_mbps,
            "Ping_ms": data['ping']['latency'],
            "Jitter_ms": data['ping']['jitter'],
            "Packet_Loss": data.get('packetLoss', 0),
            "ISP": data['isp'],
            "Server": f"{data['server']['name']} ({data['server']['location']})",
            "Result_Link": data['result']['url']
        }
        
        # Write to CSV
        file_exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
            
        print(f"Successfully logged to {LOG_FILE}")

    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")

if __name__ == "__main__":
    run_test()