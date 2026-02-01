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
import threading
import nest_asyncio

# ===== ENV =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")

SOURCE_CHANNELS = os.getenv("SOURCE_CHANNELS", "").split(",")
DEST_CHANNEL = os.getenv("DEST_CHANNEL", "")

FOOTER_TEXT = os.getenv("FOOTER_TEXT", "")
REMARK_NAME = os.getenv("REMARK_NAME", "TimeUp_VPN")
KEEP_ALIVE_PORT = int(os.getenv("KEEP_ALIVE_PORT", 8000))

# ===== FOOTERS =====
FOOTER_VITORY = """🛜 کانفیگ ویتوری
✅ تمام اپراتورها
> تست کنید اوکی بود شیر کنید واسه دوستاتون❤️‍🔥"""

FOOTER_GENERAL = """🛜 کانفیگ ویتوری
✅ تمام اپراتورها
> تست کنید اوکی بود شیر کنید واسه دوستاتون❤️‍🔥"""

FOOTER_NPVT = """🛜 کانفیگ نپسترنت
✅ تمام اپراتورها
> تست کنید اوکی بود شیر کنید واسه دوستاتون❤️‍🔥"""

# ===== CLIENT =====
client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# ===== REGEX =====
CONFIG_REGEX = re.compile(r"(?:vless|vmess|trojan)://[^\s]+", re.IGNORECASE)

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
    return f"""```
{text}
```"""

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
                caption = FOOTER_NPVT
                if FOOTER_TEXT:
                    caption += f"\n{FOOTER_TEXT}"
                await client.send_file(
                    DEST_CHANNEL,
                    msg.file.id,
                    caption=caption,
                    parse_mode=None,  # ← بدون parse_mode
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
                    caption=caption,
                    parse_mode=None,
                )
                await asyncio.sleep(1)

    # =========================
    # VLESS / VMESS / TROJAN
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
            final = cfg  # بدون تغییر Remark برای Trojan
        else:
            continue
        if final:
            final_configs.append(final)

    for cfg in final_configs:
        # کانفیگ داخل Code Block
        cfg_block = to_code_block(cfg)

        # تعیین فوتر مناسب
        footer_text = FOOTER_VITORY if "vitory" in cfg.lower() else FOOTER_GENERAL
        if FOOTER_TEXT:
            footer_text += f"\n{FOOTER_TEXT}"

        # پیام نهایی یکپارچه: Code Block + فوتر Quote واقعی
        final_message = f"""{cfg_block}
{footer_text}"""

        await client.send_message(
            DEST_CHANNEL,
            final_message,
            parse_mode=None,  # ← بدون parse_mode
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
    await client.start()
    print("NPVT + CONFIG watcher is running...")

    nest_asyncio.apply()

    def run_fastapi():
        uvicorn.run(app, host="0.0.0.0", port=KEEP_ALIVE_PORT)

    threading.Thread(target=run_fastapi, daemon=True).start()

    await client.run_until_disconnected()

client.loop.run_until_complete(main())
