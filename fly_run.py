#!/bin/bash
# Script to run the bot every hour with keep-alive

import subprocess
import time
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def health():
    return "V.I.E Alert Bot is running", 200

def run_bot_loop():
    while True:
        try:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running bot check...")
            subprocess.run(["python", "/app/run_check.py", "--hourly"], check=False)
        except Exception as e:
            print(f"Error: {e}")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Waiting 3600 seconds...")
        time.sleep(3600)

if __name__ == "__main__":
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot_loop, daemon=True)
    bot_thread.start()
    
    # Keep Flask running to satisfy Fly.io
    app.run(host='0.0.0.0', port=8080)
