from flask import Flask
from threading import Thread
import time
import subprocess
import os
from dotenv import load_dotenv

# Load environment variables from .env (for local testing)
load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    return "V.I.E Alert Bot Running", 200

def run_bot():
    print("[INIT] Bot thread started, first check in 30 seconds...")
    time.sleep(30)  # Wait 30s before first check
    
    while True:
        try:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] Running bot check...")
            result = subprocess.run(["python", "run_check.py", "--hourly"], 
                                  capture_output=True, text=True, check=False)
            print(f"[{timestamp}] Bot check completed (return code: {result.returncode})")
            if result.stdout:
                print(f"[{timestamp}] Output: {result.stdout[:200]}")
            if result.stderr:
                print(f"[{timestamp}] Errors: {result.stderr[:200]}")
        except Exception as e:
            print(f"[ERROR] {time.strftime('%Y-%m-%d %H:%M:%S')}: {e}")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Waiting 3600 seconds until next check...")
        time.sleep(3600)  # Toutes les heures

def keep_alive():
    print("[INIT] Starting Flask server...")
    t = Thread(target=run_bot)
    t.daemon = True
    t.start()
    print("[INIT] Bot thread started, Flask server listening on 0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    keep_alive()
