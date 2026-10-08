import asyncio
import base64
import csv
import gzip
import hashlib
import hmac
import html
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request
import uuid
import zipfile
from urllib.error import HTTPError
from contextlib import asynccontextmanager
from collections import deque
from pathlib import Path
from threading import Lock
from typing import Deque, Dict
from fastapi import FastAPI, Header, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.datastructures import UploadFile
import psycopg
from PIL import Image, UnidentifiedImageError
from .state import state

@state.app.get('/health')
async def health():
    return JSONResponse({
        'ok': True,
        'started_at': state.SERVICE_STARTED_AT,
        'uptime_seconds': max(0, int(time.time() - state.SERVICE_STARTED_AT)),
        'count': len(state.messages),
    })
state.register('health', health)

def compare_versions(current_version, latest_version):
    current_parts = state.normalize_version(current_version)
    latest_parts = state.normalize_version(latest_version)
    max_length = max(len(current_parts), len(latest_parts))
    current_parts = current_parts + (0,) * (max_length - len(current_parts))
    latest_parts = latest_parts + (0,) * (max_length - len(latest_parts))
    if current_parts < latest_parts:
        return -1
    if current_parts > latest_parts:
        return 1
    return 0
state.register('compare_versions', compare_versions)

async def device_status_loop():
    while True:
        await asyncio.sleep(state.DEVICE_HEARTBEAT_INTERVAL)
        now = int(time.time() * 1000)
        for device in list(state.devices.values()):
            device_id = str(device['id'])
            if state.device_online_states.get(device_id) is False:
                continue
            last_seen = int(device.get('last_seen', 0))
            online = now - last_seen <= state.DEVICE_OFFLINE_AFTER * 1000
            previous = state.device_online_states.get(device_id)
            state.device_online_states[device_id] = online
            if previous is True and (not online):
                await asyncio.to_thread(state.notify_device_status, device_id, device.get('name', 'Unknown device'), False)
state.register('device_status_loop', device_status_loop)

def extract_monitored_apps(open_apps):
    detected = []
    seen = set()
    for app_name in open_apps or []:
        title = re.sub('\\s+', ' ', str(app_name or '').strip())
        if not title:
            continue
        if state.matches_monitored_app_name(title) and title not in seen:
            detected.append(title)
            seen.add(title)
    return detected
state.register('extract_monitored_apps', extract_monitored_apps)

def get_latest_release_version(force=False):
    with state.latest_release_cache_lock:
        now = time.monotonic()
        if not force and state.latest_release_version_cache and (now < state.latest_release_cache_expires_at):
            return state.latest_release_version_cache
        if not force and (not state.latest_release_version_cache) and state.latest_release_cache_error and (now < state.latest_release_error_expires_at):
            raise RuntimeError(state.latest_release_cache_error)
        request = urllib.request.Request('https://api.github.com/repos/shadrackkiptoo/dablop/releases/latest', headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'KeyboardService-server'})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                release = json.loads(response.read().decode('utf-8'))
            latest_tag = str(release.get('tag_name', '')).strip()
            if not latest_tag:
                raise RuntimeError('GitHub release tag is empty')
        except Exception as error:
            state.latest_release_cache_error = f'Could not check GitHub releases: {error}'
            state.latest_release_error_expires_at = now + state.LATEST_RELEASE_RETRY_SECONDS
            if state.latest_release_version_cache:
                state.latest_release_cache_expires_at = now + state.LATEST_RELEASE_RETRY_SECONDS
                return state.latest_release_version_cache
            raise RuntimeError(state.latest_release_cache_error) from error
        state.latest_release_version_cache = latest_tag
        state.latest_release_cache_expires_at = now + state.LATEST_RELEASE_CACHE_SECONDS
        state.latest_release_cache_error = ''
        state.latest_release_error_expires_at = 0.0
        return latest_tag
state.register('get_latest_release_version', get_latest_release_version)

@asynccontextmanager
async def lifespan(_app):
    heartbeat_task = None
    telegram_command_task = None
    device_status_task = asyncio.create_task(state.device_status_loop())
    if state.telegram_configured():
        heartbeat_task = asyncio.create_task(state.telegram_uptime_loop())
        telegram_command_task = asyncio.create_task(asyncio.to_thread(state.poll_telegram_commands))
    elif state.TELEGRAM_BOT_TOKEN or state.TELEGRAM_CHAT_ID:
        print('Telegram uptime notifications need both TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID')
    try:
        yield
    finally:
        tasks = [device_status_task]
        if heartbeat_task:
            tasks.append(heartbeat_task)
        if telegram_command_task:
            telegram_command_task.cancel()
            tasks.append(telegram_command_task)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
state.register('lifespan', lifespan)

def matches_monitored_app_name(app_name):
    if not app_name:
        return False
    title = re.sub('\\s+', ' ', str(app_name or '').strip())
    lowered = title.lower()
    patterns = state.MONITORED_APP_PATTERNS or state.MONITORED_APP_KEYWORDS
    return any((pattern in lowered for pattern in patterns))
state.register('matches_monitored_app_name', matches_monitored_app_name)

def matches_monitored_site_url(url):
    if not url:
        return False
    patterns = state.MONITORED_SITE_PATTERNS
    if not patterns:
        return False
    parsed = urllib.parse.urlparse(str(url).strip())
    host = (parsed.netloc or parsed.path or str(url)).split(':', 1)[0].lower().strip('.')
    if not host:
        return False
    for pattern in patterns:
        pattern = str(pattern).strip().lower().strip('.')
        if not pattern:
            continue
        if host == pattern or host.endswith(f'.{pattern}'):
            return True
    return False
state.register('matches_monitored_site_url', matches_monitored_site_url)

def normalize_version(value):
    if value is None:
        return (0, 0, 0, 0, 0)
    match = re.search('(?:v)?(\\d+)(?:\\.(\\d+))?(?:\\.(\\d+))?(?:\\.(\\d+))?(?:\\.(\\d+))?', str(value).strip())
    if not match:
        return (0, 0, 0, 0, 0)
    return tuple((int(part or 0) for part in match.groups()))
state.register('normalize_version', normalize_version)

def notify_app_open_alerts(device_id, device_name, open_apps):
    if not state.telegram_configured():
        return
    device_id = str(device_id or '').strip()
    device_name = str(device_name or 'Unknown device').strip() or 'Unknown device'
    matches = state.extract_monitored_apps(open_apps)
    if not matches:
        return
    now = int(time.time())
    for app_name in matches:
        cache_key = (device_id, app_name)
        previous = state.app_open_alerts.get(cache_key)
        if previous and now - previous < 1800:
            continue
        state.app_open_alerts[cache_key] = now
        state.send_telegram_message(state.telegram_panel('ALERT // APP OPENED', f'🟢 <b>{html.escape(device_name)}</b> opened <b>{html.escape(app_name)}</b>\nID: <code>{html.escape(device_id)}</code>'))
state.register('notify_app_open_alerts', notify_app_open_alerts)

def notify_device_status(device_id, device_name, online):
    status = '🟢 online' if online else '🔴 offline'
    state.send_telegram_message(state.telegram_panel('ALERT // DEVICE STATUS', f'{status} • <b>{html.escape(device_name)}</b>\nID: <code>{html.escape(device_id)}</code>'))
state.register('notify_device_status', notify_device_status)

def notify_monitored_site_alerts(device_id, device_name, url):
    if not state.telegram_configured() or not state.matches_monitored_site_url(url):
        return
    device_id = str(device_id or '').strip()
    device_name = str(device_name or 'Unknown device').strip() or 'Unknown device'
    parsed = urllib.parse.urlparse(str(url or '').strip())
    site_host = (parsed.netloc or parsed.path or 'unknown').split(':', 1)[0].strip() or 'unknown'
    now = int(time.time())
    cache_key = (device_id, site_host)
    previous = state.site_open_alerts.get(cache_key)
    if previous and now - previous < 1800:
        return
    state.site_open_alerts[cache_key] = now
    state.send_telegram_message(state.telegram_panel('ALERT // SITE OPENED', f'🟢 <b>{html.escape(device_name)}</b> opened <b>{html.escape(site_host)}</b>\nURL: <a href="{html.escape(str(url), quote=True)}">{html.escape(str(url))}</a>\nID: <code>{html.escape(device_id)}</code>'))
state.register('notify_monitored_site_alerts', notify_monitored_site_alerts)

def telegram_devices_text():
    if not state.devices:
        return state.telegram_panel('DEVICES // NETWORK', 'No devices have checked in yet.')
    now = int(time.time() * 1000)
    online_count = 0
    lines = [f'<b>DEVICES:</b> {len(state.devices)} total', '']
    for device in sorted(state.devices.values(), key=lambda item: str(item.get('name', ''))):
        device_key = str(device.get('id', 'unknown'))
        last_seen = int(device.get('last_seen', 0))
        online = state.device_online_states.get(device_key, now - last_seen <= state.DEVICE_OFFLINE_AFTER * 1000)
        if online:
            online_count += 1
        status = '🟢 Online' if online else '🔴 Offline'
        age = state.format_uptime(max(0, (now - last_seen) // 1000))
        name = html.escape(str(device.get('name', 'Unknown device')))
        device_id = html.escape(str(device.get('id', 'unknown')))
        lines.append(f'• {status} <b>{name}</b>\n  ID: <code>{device_id}</code>\n  Last seen: {age} ago')
    lines.insert(1, f'🟢 {online_count} online  •  🔴 {len(state.devices) - online_count} offline')
    return state.telegram_panel('DEVICES // NETWORK', '\n'.join(lines))
state.register('telegram_devices_text', telegram_devices_text)

async def telegram_uptime_loop():
    await asyncio.to_thread(state.send_telegram_message, state.telegram_panel('BOOT // SERVICE ONLINE', '🟢 Link established. Built by <b>Petroholic</b>.'))
    while True:
        await asyncio.sleep(state.TELEGRAM_UPTIME_INTERVAL)
        await asyncio.to_thread(state.send_telegram_message, state.telegram_panel('PING // HEARTBEAT', f'🟢 <b>STATE:</b> HEALTHY\n⏱ <b>RUNTIME:</b> {state.format_uptime(time.time() - state.SERVICE_STARTED_AT)}'))
state.register('telegram_uptime_loop', telegram_uptime_loop)

def telegram_uptime_text():
    return state.telegram_panel('STATUS // SYSTEM HEALTH', f'🟢 <b>STATE:</b> HEALTHY\n⏱ <b>UPTIME:</b> {state.format_uptime(time.time() - state.SERVICE_STARTED_AT)}\n🗂 <b>MESSAGES:</b> {len(state.messages)}\n📱 <b>DEVICES:</b> {len(state.devices)}')
state.register('telegram_uptime_text', telegram_uptime_text)
