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

@state.app.post('/api/devices/screenshot-upload')
async def upload_device_screenshot(payload: state.ScreenshotInput, x_api_key: str | None=Header(default=None)):
    expected_key = os.getenv('INGEST_API_KEY')
    if expected_key and x_api_key != expected_key:
        return JSONResponse({'ok': False, 'error': 'unauthorized'}, status_code=401)
    device_id = payload.device_id.strip()
    screenshot_base64 = payload.screenshot_base64.strip()
    if not device_id or not screenshot_base64:
        screenshot_statuses[device_id] = {'status': 'Failed', 'message': 'The client sent an empty screenshot.', 'updated_at': int(time.time() * 1000)}
        return JSONResponse({'ok': False, 'error': 'invalid screenshot'}, status_code=400)
    if device_id not in devices:
        return JSONResponse({'ok': False, 'error': 'device not found'}, status_code=404)
    if not state.DATABASE_URL or not state.SUPABASE_URL or (not state.SUPABASE_SERVICE_ROLE_KEY):
        screenshot_statuses[device_id] = {'status': 'Failed', 'message': 'Storage configuration is missing on the server.', 'updated_at': int(time.time() * 1000)}
        return JSONResponse({'ok': False, 'error': 'screenshot storage unavailable'}, status_code=503)
    try:
        await asyncio.to_thread(state.save_screenshot, device_id, screenshot_base64)
    except (ValueError, urllib.error.URLError, TimeoutError, RuntimeError, psycopg.Error) as error:
        print(f'Could not save device screenshot: {error}')
        error_text = str(error)
        if isinstance(error, psycopg.Error):
            error_text = 'Database error while recording screenshot metadata.'
        screenshot_statuses[device_id] = {'status': 'Failed', 'message': error_text[:240] or 'The screenshot could not be saved.', 'updated_at': int(time.time() * 1000)}
        return JSONResponse({'ok': False, 'error': 'screenshot storage unavailable'}, status_code=503)
    screenshot_statuses[device_id] = {'status': 'Saved', 'message': 'Screenshot saved successfully.', 'updated_at': int(time.time() * 1000)}
    return JSONResponse({'ok': True})
state.register('upload_device_screenshot', upload_device_screenshot)
