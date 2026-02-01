from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")
SOURCE_CHANNELS = os.getenv("SOURCE_CHANNELS").split(",")

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def debug_file(event):
    print("\n===== NEW MESSAGE =====")

    msg = event.message

    print("has file:", bool(msg.file))

    if msg.file:
        f = msg.file
        print("file.name     :", repr(getattr(f, "name", None)))
        print("file.ext      :", repr(getattr(f, "ext", None)))
        print("file.mime     :", repr(getattr(f, "mime_type", None)))
        print("file.size     :", repr(getattr(f, "size", None)))
        print("file.id       :", repr(getattr(f, "id", None)))
    else:
        print("NO FILE OBJECT")

async def main():
    await client.start()
    print("DEBUG BOT RUNNING...")
    await client.run_until_disconnected()

client.loop.run_until_complete(main())
