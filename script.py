import os
import re
import tempfile
from telethon import TelegramClient, events

# ===== ENV =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE_NUMBER")

SOURCE_CHANNELS = os.getenv("SOURCE_CHANNELS").split(",")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")

# ===== CLIENT =====
client = TelegramClient("session", API_ID, API_HASH)

# ===== REGEX (FULL LINKS) =====
CONFIG_REGEX = re.compile(
    r'(?:vless|vmess)://[^\s]+',
    re.IGNORECASE
)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def watcher(event):
    found_configs = []

    # ---- TEXT OR CAPTION ----
    text = event.message.text or event.message.message
    if text:
        found_configs.extend(CONFIG_REGEX.findall(text))

    # ---- FILE (.npvt) ----
    if event.message.file and event.message.file.name.endswith(".npvt"):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            await event.message.download_media(tmp.name)
            with open(tmp.name, "r", errors="ignore") as f:
                content = f.read()
                found_configs.extend(CONFIG_REGEX.findall(content))

    # ---- SEND ONLY LINKS ----
    for cfg in set(found_configs):  # set => جلوگیری از تکراری
        await client.send_message(
            DEST_CHANNEL,
            cfg,
            link_preview=False
        )

async def main():
    await client.start(PHONE)
    print("Userbot is running...")
    await client.run_until_disconnected()

client.loop.run_until_complete(main())
