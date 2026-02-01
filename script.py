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
FOOTER_TEXT = os.getenv("FOOTER_TEXT", "")

# ===== CLIENT =====
client = TelegramClient("session", API_ID, API_HASH)

# ===== REGEX =====
CONFIG_REGEX = re.compile(r"(vless://|vmess://)", re.IGNORECASE)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def watcher(event):
    text_to_send = None

    # ---- TEXT ----
    if event.message.text:
        if CONFIG_REGEX.search(event.message.text):
            text_to_send = event.message.text

    # ---- FILE (.npvt) ----
    if event.message.file and event.message.file.name.endswith(".npvt"):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            await event.message.download_media(tmp.name)
            with open(tmp.name, "r", errors="ignore") as f:
                content = f.read()
                if CONFIG_REGEX.search(content):
                    text_to_send = content

    # ---- SEND ----
    if text_to_send:
        final_text = f"{text_to_send}\n\n{FOOTER_TEXT}".strip()
        await client.send_message(
            DEST_CHANNEL,
            final_text,
            link_preview=False
        )

async def main():
    await client.start(PHONE)
    print("Userbot is running...")
    await client.run_until_disconnected()

client.loop.run_until_complete(main())
