from flask import Flask
from threading import Thread
import time
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "V.I.E Alert Bot Running", 200

def run_bot():
    while True:
        try:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running bot check...")
            subprocess.run(["python", "run_check.py", "--hourly"], check=False)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(3600)  # Toutes les heures

def keep_alive():
    t = Thread(target=run_bot)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    keep_alive()
