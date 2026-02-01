import os
import re
import tempfile
import base64
import json
import urllib.parse
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ===== ENV =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")  # برای Railway
SOURCE_CHANNELS = os.getenv("SOURCE_CHANNELS").split(",")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")
FOOTER_TEXT = os.getenv("FOOTER_TEXT", "")
REMARK_NAME = os.getenv("REMARK_NAME", "TimeUp_VPN")

# ===== CLIENT =====
client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# ===== REGEX =====
CONFIG_REGEX = re.compile(r'(?:vless|vmess)://[^\s]+', re.IGNORECASE)

# ===== HELPERS =====
def change_vless_remark(link: str) -> str:
    base = link.split("#", 1)[0]
    return base + "#" + urllib.parse.quote(REMARK_NAME)

def change_vmess_remark(link: str) -> str | None:
    try:
        raw = link.replace("vmess://", "")
        decoded = base64.b64decode(raw + "==").decode()
        data = json.loads(decoded)
        data["ps"] = REMARK_NAME
        new_json = json.dumps(data, separators=(",", ":"))
        new_b64 = base64.b64encode(new_json.encode()).decode()
        return "vmess://" + new_b64
    except Exception:
