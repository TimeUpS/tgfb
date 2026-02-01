import os
import re
import base64
import json
import urllib.parse
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ===== ENV =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")
TEST_CHANNEL = os.getenv("TEST_CHANNEL", "@your_test_channel")
REMARK_NAME = os.getenv("REMARK_NAME", "TimeUp_VPN")
FOOTER_TEXT = os.getenv("FOOTER_TEXT", "🔹 کانفیگ تست")

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

def escape_footer_for_one_message(text: str) -> str:
    return text.replace("<", "\u003c").replace(">", "\u003e")

def group_configs(config_list):
    if not config_list:
        return None
    if len(config_list) == 1:
        return to_code_block(config_list[0])
    else:
        quote_block = "\n".join(f"> {c}" for c in config_list)
        return escape_footer_for_one_message(quote_block)

# ===== WATCHER =====
@client.on(events.NewMessage)
async def watcher(event):
    text = event.message.text or event.message.message
    if not text:
        return

    found_configs = CONFIG_REGEX.findall(text)
    final_configs = []

    for cfg in dict.fromkeys(found_configs):
        cfg = cfg.strip()
        if cfg.lower().startswith("vless://"):
            cfg = change_vless_remark(cfg)
        elif cfg.lower().startswith("vmess://"):
            cfg = change_vmess_remark(cfg)
        elif cfg.lower().startswith("trojan://"):
            pass
        else:
            continue
        if cfg:
            final_configs.append(cfg)

    final_message = group_configs(final_configs)
    if final_message:
        if final_message.startswith(">"):
            # چندتایی → Collapse Quote + Footer
            footer = escape_footer_for_one_message(FOOTER_TEXT)
            final_message += f"\n\n{footer}"
        else:
            # تک کانفیگ → Code Block + Footer
            final_message += f"\n\n{FOOTER_TEXT}"

        await client.send_message(
            TEST_CHANNEL,
            final_message,
            parse_mode="Markdown",
            link_preview=False
        )
        await asyncio.sleep(1)

# ===== RUN =====
async def main():
    await client.start()
    print("Grouped config tester is running...")
    await client.run_until_disconnected()

client.loop.run_until_complete(main())
