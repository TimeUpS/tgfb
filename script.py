import os
import re
import base64
import json
import urllib.parse
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ===== ENV =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")

SOURCE_CHANNELS = os.getenv("SOURCE_CHANNELS").split(",")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")

FOOTER_TEXT = os.getenv("FOOTER_TEXT", "")
REMARK_NAME = os.getenv("REMARK_NAME", "TimeUp_VPN")

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
    # 1️⃣ NPVT FILE (send using file.id or download)
    # =========================
    if msg.file:
        file_name = getattr(msg.file, "name", "")
        print("FILE RECEIVED:", file_name)

        if file_name and ".npvt" in file_name.lower():
            print("NPVT FILE → SEND using file.id")

            # Check if file.id is available and valid
            try:
                # Try sending with file.id directly
                await client.send_file(
                    DEST_CHANNEL,
                    msg.file.id,   # ⚡ ارسال با file.id
                    caption=file_name + (f"\n\n{FOOTER_TEXT}" if FOOTER_TEXT else "")
                )
                return  # If successful, exit here
            except Exception as e:
                print(f"Error sending file using file.id: {e}")
                print("Downloading file...")

            # =========================
            # 2️⃣ Download file with the same name
            # =========================
            # مسیر فایل با نام اصلی
            file_path = f"/path/to/your/directory/{file_name}"

            # دانلود فایل با نام مورد نظر
            await msg.download_media(file_path)

            # ارسال فایل با نام جدید
            await client.send_file(
                DEST_CHANNEL,
                file_path,
                caption=(f"\n\n{FOOTER_TEXT}" if FOOTER_TEXT else "")
            )

    # =========================
    # 2️⃣ VLESS / VMESS TEXT (Code Block + Rename Remark)
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
            link_preview=False
        )

# ===== RUN =====
async def main():
    await client.start()
    print("NPVT + CONFIG watcher is running...")
    await client.run_until_disconnected()

client.loop.run_until_complete(main())
