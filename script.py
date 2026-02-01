import os
import re
import base64
import json
import urllib.parse
import asyncio
from fastapi import FastAPI
import uvicorn
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import tempfile

# ===== ENV =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")

SOURCE_CHANNELS = os.getenv("SOURCE_CHANNELS").split(",")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")

FOOTER_TEXT = os.getenv("FOOTER_TEXT", "")
REMARK_NAME = os.getenv("REMARK_NAME", "TimeUp_VPN")
KEEP_ALIVE_PORT = int(os.getenv("KEEP_ALIVE_PORT", 8000))

# ===== CLIENT =====
client = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH
)

# ===== REGEX =====
CONFIG_REGEX = re.compile(r"(?:vless|vmess)://[^\s]+", re.IGNORECASE)

# ===== HELPERS =====
def change_vless_remark(link: str) -> str:
    base = link.split("#", 1)[0]
    return base + "#" + urllib.parse.quote(REMARK_NAME)

def change_vmess_remark(link: str):
    try:
        raw = link.replace("vmess://", "")
        decoded = base64.b64decode(raw + "==").decode()
        data = json.loads(decoded)
        data["ps"] = REMARK_NAME
        new_json = json.dumps(data, separators=(",", ":"))
        new_b64 = base64.b64encode(new_json.encode()).decode()
        return "vmess://" + new_b64
    except Exception:
        return None

def to_code_block(text: str) -> str:
    return f"```\n{text}\n```"

# ===== WATCHER =====
@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def watcher(event):
    msg = event.message

    # =========================
    # NPVT FILE
    # =========================
    if msg.file:
        file_name = getattr(msg.file, "name", "")
        if file_name and ".npvt" in file_name.lower():
            try:
                await client.send_file(
                    DEST_CHANNEL,
                    msg.file.id,
                    caption="🛜 کانفیگ نپسترنت" + (f"\n\n{FOOTER_TEXT}" if FOOTER_TEXT else "")
                )
                await asyncio.sleep(1)
                return
            except Exception as e:
                print(f"Error sending file.id: {e}, downloading file...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".npvt") as tmp:
                    file_path = await msg.download_media(tmp.name)
                await client.send_file(
                    DEST_CHANNEL,
                    file_path,
                    caption="🛜 کانفیگ نپسترنت" + (f"\n\n{FOOTER_TEXT}" if FOOTER_TEXT else "")
                )
                await asyncio.sleep(1)

    # =========================
    # VLESS / VMESS
    # =========================
    text = msg.text or msg.message
    if not text:
        return

    found_configs = CONFIG_REGEX.findall(text)
    if not found_configs:
        return

    final_configs = []
    for cfg in set(found_configs):
        cfg = cfg.strip()
        if cfg.lower().startswith("vless://"):
            final = change_vless_remark(cfg)
        elif cfg.lower().startswith("vmess://"):
            final = change_vmess_remark(cfg)
        elif cfg.lower().startswith("trojan://"):
            final = change_vmess_remark(cfg)
        else:
            continue
        if final:
            final_configs.append(final)

    for cfg in final_configs:
        message = to_code_block(cfg)
        if FOOTER_TEXT:
            message = "🛜 کانفیگ ویتوری" + (f"\n\n{FOOTER_TEXT}" if FOOTER_TEXT else "")
        await client.send_message(
            DEST_CHANNEL,
            message,
            link_preview=False
        )
        await asyncio.sleep(1)

# ===== FASTAPI KEEP-ALIVE =====
app = FastAPI()

@app.get("/ping")
async def ping():
    return {"status": "ok"}

# ===== RUN =====
async def main():
    # ران کردن Telethon
    await client.start()
    print("NPVT + CONFIG watcher is running...")

    # ران کردن FastAPI در یک تسک جداگانه
    import nest_asyncio
    nest_asyncio.apply()
    import threading

    def run_fastapi():
        uvicorn.run(app, host="0.0.0.0", port=KEEP_ALIVE_PORT)

    threading.Thread(target=run_fastapi, daemon=True).start()

    # بات تلگرام تا زمانی که قطع نشود ران بماند
    await client.run_until_disconnected()

client.loop.run_until_complete(main())
