import os
import time
from collections import deque
from pathlib import Path
from threading import Lock
from types import SimpleNamespace
from fastapi import FastAPI
class Runtime(SimpleNamespace):
    def register(self,name,value):
        setattr(self,name,value)
        self._functions[name]=value
    def __getattr__(self,name):
        try: return self._functions[name]
        except KeyError: raise AttributeError(name) from None
state=Runtime(_functions={})
state.app=FastAPI(title="KeyboardService")
state.MAX_MESSAGES=200
state.BASE_DIR=Path(__file__).resolve().parent.parent
state.LOG_PATH=state.BASE_DIR/"text.txt"
state.HTML_PATH=state.BASE_DIR/"web"/"index.html"
state.messages=deque(maxlen=state.MAX_MESSAGES)
state.devices={}
state.device_online_states={}
state.screenshot_requests={}
state.screenshot_commands={}
state.device_command_records={}
state.screenshot_statuses={}
state.input_block_timers={}
state.DATABASE_URL=os.getenv("DATABASE_URL","").strip()
state.SUPABASE_URL=os.getenv("SUPABASE_URL","").strip().rstrip("/")
state.SUPABASE_SERVICE_ROLE_KEY=os.getenv("SUPABASE_SERVICE_ROLE_KEY","").strip()
state.SCREENSHOT_BUCKET="screenshots"
state.MAX_MESSAGE_IMAGE_BYTES=10*1024*1024
state.MESSAGE_IMAGE_EXTENSIONS={"JPEG":"jpg","PNG":"png","GIF":"gif","WEBP":"webp"}
state.MAX_MESSAGE_DOCUMENT_BYTES=20*1024*1024
state.MESSAGE_DOCUMENT_MIME_TYPES={"pdf":"application/pdf","docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document","rtf":"application/rtf","txt":"text/plain; charset=utf-8"}
state.SERVICE_STARTED_AT=time.time()
state.DEVICE_HEARTBEAT_INTERVAL=30
state.DEVICE_OFFLINE_AFTER=45
state.SCREENSHOT_STATUS_TIMEOUT=90
state.SCREENSHOT_LIST_LIMIT=30
state.LATEST_RELEASE_CACHE_SECONDS=300
state.LATEST_RELEASE_RETRY_SECONDS=30
state.latest_release_version_cache=""
state.latest_release_cache_expires_at=0.0
state.latest_release_cache_error=""
state.latest_release_error_expires_at=0.0
state.latest_release_cache_lock=Lock()
state.TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
state.TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID","").strip()
state.APP_USERNAME=os.getenv("APP_USERNAME","").strip()
state.APP_PASSWORD=os.getenv("APP_PASSWORD","").strip()
state.APP_SESSION_SECRET=os.getenv("APP_SESSION_SECRET","keyboardservice-secret").strip() or "keyboardservice-secret"
state.CLIENT_SITE_URL=os.getenv("SITE_URL","").strip().rstrip("/")
state.BUY_ME_A_COFFEE_URL=os.getenv("BUY_ME_A_COFFEE_URL","https://buymeacoffee.com/yourusername").strip()
state.TELEGRAM_UPTIME_INTERVAL=max(60,int(os.getenv("TELEGRAM_UPTIME_INTERVAL_SECONDS","900")))
state.DEFAULT_MONITORED_APP_KEYWORDS=("chrome","chromium","edge","firefox","brave","opera","vivaldi","arc","iexplore","safari","morelogin","gologin","multilogin","browser")
state.MONITORED_APP_KEYWORDS=state.DEFAULT_MONITORED_APP_KEYWORDS
state.MONITORED_APP_FILE=os.path.join(state.BASE_DIR,"monitored_apps.json")
state.MONITORED_SITE_FILE=os.path.join(state.BASE_DIR,"monitored_sites.json")
state.MONITORED_APP_PATTERNS=()
state.MONITORED_SITE_PATTERNS=()
state.SUPPORT_METHODS=[]
state.app_open_alerts={}
state.site_open_alerts={}
state.events=[]
state.raw_history=[]
