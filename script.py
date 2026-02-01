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
        pass

def to_code_block(text: str) -> str:
    return f"```\n{text}\n```"

# ===== WATCHER =====
@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def watcher(event):
    found_configs = []

    # ---- TEXT / CAPTION ----
    text = event.message.text or event.message.message
    if text:
        found_configs.extend(CONFIG_REGEX.findall(text))

    # ---- FILE (.npvt یا هر فایل متنی) ----
    if event.message.file:
    try:
        # دانلود فایل داخل async function
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            file_path = await event.message.download_media(tmp.name)

        # خواندن فایل به عنوان متن
        with open(file_path, "r", errors="ignore") as f:
            content = f.read()
            # regex روی کل محتوا اجرا می‌کنیم
            found_configs.extend(CONFIG_REGEX.findall(content))

    except Exception:
        pass


    # ---- PROCESS & SEND ----
    final_configs = []

    for cfg in set(found_configs):
        cfg = cfg.strip()

        if cfg.lower().startswith("vless://"):
            final = change_vless_remark(cfg)
        elif cfg.lower().startswith("vmess://"):
            final = change_vmess_remark(cfg)
        else:
            continue

        if final:
            final_configs.append(final)

    for cfg in final_configs:
        message = to_code_block(cfg)

        if FOOTER_TEXT:
            message = f"{message}\n\n{FOOTER_TEXT}"

        await client.send_message(
            DEST_CHANNEL,
            message,
            link_preview=False,
            parse_mode="markdown"
        )

# ===== RUN =====
async def main():
    await client.start()
    print("Userbot is running...")
    await client.run_until_disconnected()

client.loop.run_until_complete(main())
