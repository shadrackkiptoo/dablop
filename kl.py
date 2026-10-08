import threading
import time

from pynput.keyboard import Key, KeyCode, Listener

count = 0
text_buffer = ""
message_buffer = ""
last_key_time_ms = None
message_started_ms = None
flush_timer = None
active_modifiers = set()
MESSAGE_GAP_MS = 1200

SHIFTED_SYMBOLS = {
    "1": "!",
    "2": "@",
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "^",
    "7": "&",
    "8": "*",
    "9": "(",
    "0": ")",
    "-": "_",
    "=": "+",
    "[": "{",
    "]": "}",
    "\\": "|",
    ";": ":",
    "'": '"',
    ",": "<",
    ".": ">",
    "/": "?",
    "`": "~",
}


def format_message_entry(timestamp_ms, text):
    return f"{int(timestamp_ms)}|{text}"


def should_start_new_bubble(last_key_time_ms_value, current_time_ms, current_text):
    if not current_text:
        return False
    if last_key_time_ms_value is None:
        return False
    return (current_time_ms - last_key_time_ms_value) >= MESSAGE_GAP_MS


def flush_current_message(force=False):
    global text_buffer, message_buffer, last_key_time_ms, message_started_ms, flush_timer

    if not message_buffer:
        flush_timer = None
        return

    if force or (last_key_time_ms is not None and time.time() * 1000 - last_key_time_ms >= MESSAGE_GAP_MS):
        entry_ts = message_started_ms if message_started_ms is not None else last_key_time_ms
        text_buffer = (text_buffer + ("\n" if text_buffer else "") + format_message_entry(entry_ts, message_buffer)).rstrip("\n")
        print(f"\n[Bubble] {message_buffer}")
        message_buffer = ""
        last_key_time_ms = None
        message_started_ms = None
        flush_timer = None
        write_file()


def schedule_flush():
    global flush_timer

    if flush_timer is not None:
        flush_timer.cancel()

    flush_timer = threading.Timer(MESSAGE_GAP_MS / 1000.0, flush_current_message, args=(True,))
    flush_timer.daemon = True
    flush_timer.start()


def write_file():
    with open("text.txt", "w", encoding="utf-8") as f:
        f.write(text_buffer)


def normalize_key(key, modifiers=None):
    modifiers = modifiers or set()

    if key in (Key.shift, Key.shift_l, Key.shift_r):
        return ""
    if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
        return ""
    if key in (Key.alt, Key.alt_l, Key.alt_r):
        return ""
    if key in (Key.cmd, Key.cmd_l, Key.cmd_r):
        return ""
    if key == Key.space:
        return " "
    if key == Key.enter:
        return "\n"
    if key == Key.tab:
        return "\t"
    if key == Key.backspace:
        return "\b"

    if isinstance(key, KeyCode) and key.char is not None:
        ch = key.char
        if Key.shift in modifiers and ch.isalpha():
            ch = ch.upper()
        elif Key.shift in modifiers and ch in SHIFTED_SYMBOLS:
            ch = SHIFTED_SYMBOLS[ch]
        return ch

    return ""


def on_press(key):
    global text_buffer, count, active_modifiers, message_buffer, last_key_time_ms, message_started_ms

    if key in (Key.shift, Key.shift_l, Key.shift_r):
        active_modifiers.add(Key.shift)
        return
    if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
        active_modifiers.add(Key.ctrl)
        return
    if key in (Key.alt, Key.alt_l, Key.alt_r):
        active_modifiers.add(Key.alt)
        return
    if key in (Key.cmd, Key.cmd_l, Key.cmd_r):
        active_modifiers.add(Key.cmd)
        return

    symbol = normalize_key(key, active_modifiers)
    if not symbol:
        return

    now_ms = time.time() * 1000

    if symbol == "\b":
        if message_buffer:
            message_buffer = message_buffer[:-1]
        schedule_flush()
        return

    if symbol == "\n":
        flush_current_message(force=True)
        return

    if message_buffer and should_start_new_bubble(last_key_time_ms, now_ms, message_buffer):
        flush_current_message(force=True)

    if message_started_ms is None:
        message_started_ms = now_ms

    message_buffer += symbol
    last_key_time_ms = now_ms
    count += 1
    print(symbol, end="", flush=True)
    schedule_flush()


def on_release(key):
    if key in (Key.shift, Key.shift_l, Key.shift_r):
        active_modifiers.discard(Key.shift)
    elif key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
        active_modifiers.discard(Key.ctrl)
    elif key in (Key.alt, Key.alt_l, Key.alt_r):
        active_modifiers.discard(Key.alt)
    elif key in (Key.cmd, Key.cmd_l, Key.cmd_r):
        active_modifiers.discard(Key.cmd)


def run_listener():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        print("\nRunning... press Ctrl+C in the console to stop.")
        listener.join()


if __name__ == "__main__":
    text_buffer = ""
    write_file()
    run_listener()