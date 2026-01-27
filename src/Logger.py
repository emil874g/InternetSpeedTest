import subprocess
import json
import csv
import os
import platform
import time
from datetime import datetime

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_OS = platform.system()

# 1. Path to the Speedtest engine
if SYSTEM_OS == "Windows":
    SPEEDTEST_CMD = os.path.join(SCRIPT_DIR, "speedtest.exe")
else:
    SPEEDTEST_CMD = "/usr/local/bin/speedtest"

# 2. Define locations
# Keeping the local log in the ROOT folder (one level up from 'Python' folder)
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LOCAL_LOG = os.path.join(BASE_DIR, "office_internet_speeds.csv")
HEARTBEAT_LOG = os.path.join(BASE_DIR, "heartbeat.log")

if SYSTEM_OS == "Darwin":
    CLOUD_LOG = "/Users/emillydersen/Library/CloudStorage/GoogleDrive-emilbdl@gmail.com/Mit drev/SpeedTest/office_speeds.csv"
else:
    CLOUD_LOG = r"C:\Users\arh\My Drive\SpeedTest\office_speeds.csv"

# --- HELPER FUNCTIONS ---

def write_heartbeat(message):
    """Logs script status to a plain text file for debugging."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HEARTBEAT_LOG, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def save_to_csv(file_path, data_row):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file_exists = os.path.isfile(file_path)
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data_row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data_row)
        print(f"Successfully logged to {file_path}")
    except Exception as e:
        write_heartbeat(f"CSV WRITE ERROR: {e}")
        print(f"Failed to write to {file_path}: {e}")

def run_test():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting Speedtest...")
    
    if SYSTEM_OS == "Windows" and not os.path.exists(SPEEDTEST_CMD):
        write_heartbeat("ERROR: speedtest.exe missing")
        return

    try:
        # Run test
        cmd = [SPEEDTEST_CMD, '-f', 'json', '--accept-license']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            write_heartbeat(f"SPEEDTEST CLI ERROR: {result.stderr}")
            return

        data = json.loads(result.stdout)
        download_mbps = round(data['download']['bandwidth'] / 125000, 2)
        upload_mbps = round(data['upload']['bandwidth'] / 125000, 2)
        
        # Row with explicit units in headers for easier visualization
        row = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Device": platform.node(),
            "Download_Mbps": download_mbps,
            "Upload_Mbps": upload_mbps,
            "Ping_ms": data['ping']['latency'],
            "Jitter_ms": data['ping']['jitter'],
            "Packet_Loss_Pct": data.get('packetLoss', 0),
            "ISP": data['isp'],
            "Server": f"{data['server']['name']} ({data['server']['location']})",
            "Result_Link": data['result']['url']
        }
        
        save_to_csv(LOCAL_LOG, row)
        save_to_csv(CLOUD_LOG, row)

    except Exception as e:
        write_heartbeat(f"CRITICAL FAILURE: {e}")
        print(f"CRITICAL FAILURE: {e}")

# --- MAIN EXECUTION LOOP ---

if __name__ == "__main__":
    NUM_TESTS = 4
    WAIT_TIME = 300 # 5 minutes
    
    write_heartbeat(f"--- SESSION START: Requesting {NUM_TESTS} tests ---")
    
    for i in range(NUM_TESTS):
        run_test()
        
        # Don't sleep after the very last test
        if i < (NUM_TESTS - 1):
            print(f"Test {i+1} complete. Waiting 5 minutes...")
            time.sleep(WAIT_TIME)
            
    write_heartbeat("--- SESSION END: All tests finished ---")