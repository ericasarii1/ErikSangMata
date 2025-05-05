import os
import logging
import asyncio
import aiosqlite
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv

# Logging terminal
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Load environment
load_dotenv()

api_id = int(os.getenv("API_ID", "23746013"))
api_hash = os.getenv("API_HASH", "c4c86f53aac9b29f7fa28d5ba953be44")
bot_token = os.getenv("BOT_TOKEN", "7547900184:AAHG_FIFns7DSI4jtPSnQ726yO3yB3BnEzY")
log_channel = int(os.getenv("LOG_CHANNEL_ID", "-1002518891874"))

app = Client("sangmata_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
usernames = {}

# Inisialisasi database
async def init_db():
    async with aiosqlite.connect("history.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                user_id INTEGER,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# Simpan riwayat ke database
async def save_history(uid, first_name, last_name, username):
    async with aiosqlite.connect("history.db") as db:
        await db.execute("""
            INSERT INTO history (user_id, first_name, last_name, username)
            VALUES (?, ?, ?, ?)
        """, (uid, first_name, last_name, username))
        await db.commit()

@app.on_message(filters.group | filters.private)
async def track_user(client: Client, message: Message):
    user = message.from_user
    if not user or user.is_bot:
        return

    uid = user.id
    current = (user.first_name or "", user.last_name or "", user.username or "")
    old = usernames.get(uid)

    if old and old != current:
        old_name = f"{old[0]} {old[1]}".strip()
        new_name = f"{current[0]} {current[1]}".strip()
        old_username = f"@{old[2]}" if old[2] else "❌ Tidak ada"
        new_username = f"@{current[2]}" if current[2] else "❌ Tidak ada"

        text = (
            f"⚠️ **Perubahan Deteksi Identitas!**\n"
            f"👤 {new_name} ({uid})\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 **Nama Lama:** {old_name}\n"
            f"🔖 **Username Lama:** {old_username}\n"
            f"🆕 **Nama Baru:** {new_name}\n"
            f"🏷️ **Username Baru:** {new_username}"
        )

        await message.reply(text)
        await client.send_message(log_channel, text)
        await save_history(uid, *old)

    if not old:
        await save_history(uid, *current)

    usernames[uid] = current

if __name__ == "__main__":
    logging.info("✅ Memulai bot SangMata Clone...")
    asyncio.get_event_loop().run_until_complete(init_db())
    app.run()
