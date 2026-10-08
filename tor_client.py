import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path

import requests

DEFAULT_ENDPOINT = os.getenv(
    "TOR_ENDPOINT",
    "https://your-app-name.onrender.com/api/telemetry",
)
DEFAULT_AUTH = os.getenv("CLIENT_AUTH_SECRET", "your_secret_passphrase")
TOR_PROXY = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050",
}


def get_tor_path():
    if hasattr(sys, "_MEIPASS"):
        candidate = Path(sys._MEIPASS) / "tor.exe"
        if candidate.exists():
            return str(candidate)
    local_candidate = Path.cwd() / "tor.exe"
    if local_candidate.exists():
        return str(local_candidate)
    return ""


def launch_tor_silently():
    tor_path = get_tor_path()
    if not tor_path:
        print("Tor executable not found. Skipping local launch.")
        return False

    data_dir = Path(tempfile.gettempdir()) / "tor-render-pipeline"
    data_dir.mkdir(exist_ok=True)

    subprocess.Popen(
        [
            tor_path,
            "--SocksPort",
            "9050",
            "--DataDirectory",
            str(data_dir),
        ],
        creationflags=0x08000000,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
    time.sleep(6)
    return True


def send_data(payload):
    try:
        response = requests.post(
            DEFAULT_ENDPOINT,
            json=payload,
            proxies=TOR_PROXY,
            headers={"Authorization": f"Bearer {DEFAULT_AUTH}"},
            timeout=20,
        )
        return response.status_code == 200, response.status_code, response.text
    except Exception as error:
        return False, None, str(error)


if __name__ == "__main__":
    launch_tor_silently()
    payload = {
        "device_id": os.getenv("DEVICE_ID", "remote-pc-01"),
        "status": "Online",
        "source": "tor_client.py",
    }

    ok, status_code, text = send_data(payload)
    if ok:
        print(f"Telemetry sent successfully: {status_code}")
    else:
        print(f"Telemetry failed: {status_code} {text}")
