import subprocess
import json
import csv
import os
import platform
import time
from datetime import datetime, timedelta

# --- CONFIGURATION ---

# Get the directory where this script lives (/app/scripts)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the root (/app), then into /data
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "data")
LOCAL_LOG = os.path.join(DATA_DIR, "office_internet_speeds.csv")
HEARTBEAT_LOG = os.path.join(DATA_DIR, "heartbeat.log")

# Ensure the folder exists before writing
os.makedirs(DATA_DIR, exist_ok=True) 

SPEEDTEST_CMD = "speedtest"

# --- HELPER FUNCTIONS ---
def write_heartbeat(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HEARTBEAT_LOG, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def save_to_csv(file_path, data_row):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        file_exists = os.path.isfile(file_path)
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data_row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data_row)
    except Exception as e:
        write_heartbeat(f"CSV WRITE ERROR: {e}")

def run_test():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running Speedtest...")
    try:
        cmd = [SPEEDTEST_CMD, '-f', 'json', '--accept-license', '--accept-gdpr']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            write_heartbeat(f"SPEEDTEST CLI ERROR: {result.stderr}")
            return

        data = json.loads(result.stdout)
        
        row = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Device": platform.node(),
            "Download_Mbps": round(data['download']['bandwidth'] / 125000, 2),
            "Upload_Mbps": round(data['upload']['bandwidth'] / 125000, 2),
            "Ping_ms": data['ping']['latency'],
            "Jitter_ms": data['ping']['jitter'],
            "Packet_Loss_Pct": data.get('packetLoss', 0),
            "ISP": data['isp'],
            "Server": f"{data['server']['name']} ({data['server']['location']})",
            "Result_Link": data['result']['url']
        }
        
        save_to_csv(LOCAL_LOG, row)
        print(f"  -> Logged: {row['Download_Mbps']} Mbps Down / {row['Upload_Mbps']} Mbps Up")

    except Exception as e:
        write_heartbeat(f"CRITICAL FAILURE: {e}")

# --- MAIN EXECUTION LOOP ---
if __name__ == "__main__":
    NUM_TESTS = 4
    WAIT_TIME = 300  # 5 minutes
    
    write_heartbeat("--- SESSION START: Docker background logger initialized ---")
    print("🚀 Docker Logger Started! Running 24/7 background service...")

    while True:
        # 1. Run the batch of 4 tests
        print(f"\n--- Starting hourly batch of {NUM_TESTS} tests ---")
        for i in range(NUM_TESTS):
            run_test()
            
            if i < (NUM_TESTS - 1):
                print(f"  -> Waiting 5 minutes until next test...")
                time.sleep(WAIT_TIME)
        
        # 2. Batch complete. Calculate exactly how many seconds until the NEXT full hour
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        seconds_to_sleep = (next_hour - now).total_seconds()
        
        minutes_to_sleep = int(seconds_to_sleep / 60)
        print(f"\n✅ Hourly batch complete. Sleeping for {minutes_to_sleep} minutes until {next_hour.strftime('%H:%M:%S')}...")
        write_heartbeat(f"Batch complete. Sleeping until {next_hour.strftime('%H:%M:%S')}")
        
        # 3. Sleep until the top of the hour (Uses practically 0% CPU)
        time.sleep(seconds_to_sleep)
