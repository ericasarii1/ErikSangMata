import os, logging
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

load_dotenv()

# Konfigurasi
api_id = int(os.getenv("API_ID", ""))
api_hash = os.getenv("API_HASH", "")
bot_token = os.getenv("BOT_TOKEN", "")

app = Client("sangmata_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
usernames = {}

@app.on_message(filters.group)
async def track_user(client: Client, message: Message):
    user = message.from_user
    if not user or user.is_bot: return

    uid = user.id
    current = (user.first_name or "", user.last_name or "", user.username or "")
    old = usernames.get(uid)

    if old and old != current:
        old_name = f"{old[0]} {old[1]}".strip()
        new_name = f"{current[0]} {current[1]}".strip()
        old_username = f"@{old[2]}" if old[2] else "❌ Tidak ada"
        new_username = f"@{current[2]}" if current[2] else "❌ Tidak ada"

        await message.reply(
            f"⚠️ **Perubahan Deteksi Identitas!**\n"
            f"👤 [{user.first_name}](tg://user?id={uid}) (`{uid}`)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 **Nama Lama:** `{old_name}`\n"
            f"🔖 **Username Lama:** `{old_username}`\n"
            f"🆕 **Nama Baru:** `{new_name}`\n"
            f"🏷️ **Username Baru:** `{new_username}`"
        )

    usernames[uid] = current

if __name__ == "__main__":
    logging.info("🚀 SangMata Bot siap mengawasi perubahan identitas!")
    app.run()
