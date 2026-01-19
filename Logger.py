import subprocess
import json
import csv
import os
import platform
from datetime import datetime

# --- INTELLIGENT CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Determine OS and set binary name
SYSTEM_OS = platform.system() # Returns 'Windows' or Mac/Linux

if SYSTEM_OS == "Windows":
    # On the Lenovo, we expect speedtest.exe to be in the SAME folder as this script
    SPEEDTEST_CMD = os.path.join(SCRIPT_DIR, "speedtest.exe")
else:
    # On Mac/Linux, we assume it's installed via Brew/Apt and is in the global PATH
    # If this fails, you can hardcode the path like "/opt/homebrew/bin/speedtest"
    SPEEDTEST_CMD = "speedtest" 

# 2. Log File Path (Saves to the repo folder by default)
LOG_FILE = os.path.join(SCRIPT_DIR, "office_internet_speeds.csv")
# ---------------------------------

def run_test():
    print(f"[{datetime.now()}] Running on {SYSTEM_OS}...")
    
    # Check if Windows binary exists before running
    if SYSTEM_OS == "Windows" and not os.path.exists(SPEEDTEST_CMD):
        print(f"CRITICAL ERROR: 'speedtest.exe' not found in {SCRIPT_DIR}")
        print("Please download the Windows CLI from Ookla and place it here.")
        return

    try:
        # Run the command
        cmd = [SPEEDTEST_CMD, '-f', 'json', '--accept-license']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Speedtest Error: {result.stderr}")
            return

        data = json.loads(result.stdout)
        
        # Parse Data
        row = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Device": platform.node(), # Logs which machine ran the test
            "Download_Mbps": round(data['download']['bandwidth'] / 125000, 2),
            "Upload_Mbps": round(data['upload']['bandwidth'] / 125000, 2),
            "Ping_ms": data['ping']['latency'],
            "Link": data['result']['url']
        }
        
        # Save to CSV
        file_exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, 'a', newline='') as f: 
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
            
        print(f"Success! {row['Download_Mbps']} Mbps logged.")

    except Exception as e:
        print(f"Script Crashed: {e}")

if __name__ == "__main__":
    run_test()