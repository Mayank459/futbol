"""Streamlit Keep-Alive Daemon & Watchdog Service.

Ensures the Streamlit Dashboard never dies, sleeps, or crashes.
Features:
1. Spawns Streamlit in headless mode on port 8501.
2. Periodically pings the Streamlit health endpoint (http://localhost:8501/_stcore/health).
3. If Streamlit crashes or becomes unresponsive, automatically restarts it immediately.
4. Auto-reconnects and logs heartbeat timestamps.
"""

import os
import sys
import time
import subprocess
import urllib.request
from datetime import datetime

PORT = 8501
HEALTH_URL = f"http://localhost:{PORT}/_stcore/health"
APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "dashboard", "app.py"))
CHECK_INTERVAL_SEC = 10
MAX_UNRESPONSIVE_RETRIES = 3


def is_server_healthy() -> bool:
    """Pings Streamlit's internal health check endpoint."""
    try:
        req = urllib.request.Request(HEALTH_URL, headers={"User-Agent": "Watchdog/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_streamlit_process() -> subprocess.Popen:
    """Launches the Streamlit process."""
    cmd = [
        sys.executable, "-m", "streamlit", "run", APP_PATH,
        f"--server.port={PORT}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.runOnSave=true"
    ]
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Spawning Streamlit on port {PORT}...")
    sys.stdout.flush()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc


def run_watchdog():
    print("=" * 65)
    print("STREAMLIT KEEP-ALIVE WATCHDOG ACTIVE")
    print(f"Target: {APP_PATH}")
    print(f"Health Check: {HEALTH_URL} (Every {CHECK_INTERVAL_SEC}s)")
    print("=" * 65)
    sys.stdout.flush()

    process = start_streamlit_process()
    # Initial grace period for startup
    time.sleep(5)

    unresponsive_count = 0

    try:
        while True:
            # Check 1: Process death
            ret_code = process.poll()
            if ret_code is not None:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚠️ Streamlit process exited with code {ret_code}. Auto-restarting...")
                process = start_streamlit_process()
                time.sleep(5)
                unresponsive_count = 0
                continue

            # Check 2: HTTP Health check
            if is_server_healthy():
                unresponsive_count = 0
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟢 Heartbeat OK - Streamlit is active at http://localhost:{PORT}")
            else:
                unresponsive_count += 1
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🟡 Health check failed ({unresponsive_count}/{MAX_UNRESPONSIVE_RETRIES})")

                if unresponsive_count >= MAX_UNRESPONSIVE_RETRIES:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔴 Process unresponsive. Terminating and rebooting...")
                    try:
                        process.kill()
                    except Exception:
                        pass
                    process = start_streamlit_process()
                    time.sleep(5)
                    unresponsive_count = 0

            sys.stdout.flush()
            time.sleep(CHECK_INTERVAL_SEC)

    except KeyboardInterrupt:
        print("\nStopping Watchdog and terminating Streamlit...")
        try:
            process.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    run_watchdog()

