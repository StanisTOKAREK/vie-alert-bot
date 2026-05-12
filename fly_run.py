#!/usr/bin/env python3
"""Run the V.I.E bot at the top of every hour, with a Flask keep-alive for Fly.io."""

import subprocess
import time
import threading
from datetime import datetime, timedelta

from flask import Flask

app = Flask(__name__)


@app.route('/')
def health():
    return "V.I.E Alert Bot is running", 200


def seconds_until_next_hour(now: datetime) -> float:
    """Seconds from `now` until the next HH:00:00. Always > 0."""
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return (next_hour - now).total_seconds()


DAILY_DIGEST_HOUR_UTC = 6  # 8h Paris (UTC+2 en été)


def run_bot_loop():
    while True:
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        # Daily digest at 8h Paris (6h UTC); alert-only mode the rest of the time
        args = ["python", "/app/run_check.py"]
        if now.hour == DAILY_DIGEST_HOUR_UTC:
            args.append("--daily")
        print(f"[{timestamp}] Running bot check ({' '.join(args[2:] or ['alert-only'])})...", flush=True)
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=False,
            )
            print(f"[{timestamp}] Bot check exited with code {result.returncode}", flush=True)
            if result.stdout:
                print(f"[{timestamp}] stdout: {result.stdout.strip()}", flush=True)
            if result.stderr:
                print(f"[{timestamp}] stderr: {result.stderr.strip()}", flush=True)
        except Exception as e:
            print(f"[{timestamp}] Error: {e}", flush=True)

        delay = seconds_until_next_hour(datetime.now())
        wake_at = (datetime.now() + timedelta(seconds=delay)).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] Sleeping {delay:.0f}s until next top of hour ({wake_at})", flush=True)
        time.sleep(delay)


if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot_loop, daemon=True)
    bot_thread.start()
    app.run(host='0.0.0.0', port=8080)