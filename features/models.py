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

class DeviceHeartbeat(BaseModel):
    device_id: str
    device_name: str = 'Unknown device'
    client_version: str = ''
    started_at: int
    local_time: str = ''
    local_time_ms: int | None = None
    local_ip: str = ''
    logged_in_user: str = ''
    battery_percent: int | None = None
    battery_status: str = 'Unknown'
    open_apps: list[str] = []
state.register('DeviceHeartbeat', DeviceHeartbeat)

class DeviceOffline(BaseModel):
    device_id: str
state.register('DeviceOffline', DeviceOffline)

class MessageInput(BaseModel):
    message_id: int | None = None
    text: str
    raw_text: str = ''
    raw_only: bool = False
    device_id: str = 'unknown'
    device_name: str = 'Unknown device'
    app_name: str = 'Unknown app'
    source_url: str = ''
    is_pasted: bool = False
    is_copied: bool = False
    retry: bool = False
state.register('MessageInput', MessageInput)

class RawBatchInput(BaseModel):
    batch_id: str
    device_id: str
    device_name: str = 'Unknown device'
    session_id: str
    started_at: int
    ended_at: int
    event_count: int
    payload_base64: str
state.register('RawBatchInput', RawBatchInput)

class ScreenshotInput(BaseModel):
    device_id: str
    screenshot_base64: str
state.register('ScreenshotInput', ScreenshotInput)

class ScreenshotStatusInput(BaseModel):
    device_id: str
    status: str
    message: str = ''
state.register('ScreenshotStatusInput', ScreenshotStatusInput)
