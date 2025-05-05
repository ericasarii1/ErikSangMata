import os
import logging
import asyncio
import aiosqlite
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Load environment
load_dotenv()

api_id = int(os.getenv("API_ID", ""))
api_hash = os.getenv("API_HASH", "")
bot_token = os.getenv("BOT_TOKEN", "")
log_channel = int(os.getenv("LOG_CHANNEL_ID", ""))

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

# Simpan riwayat
async def save_history(uid, first_name, last_name, username):
    async with aiosqlite.connect("history.db") as db:
        await db.execute("""
            INSERT INTO history (user_id, first_name, last_name, username)
            VALUES (?, ?, ?, ?)
        """, (uid, first_name, last_name, username))
        await db.commit()

# Lacak perubahan identitas
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
            f"👤 {new_name} (`{uid}`)\n"
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

# Perintah /riwayat: lihat riwayat berdasarkan ID
@app.on_message(filters.command("riwayat") & (filters.group | filters.private))
async def show_history(client: Client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            target_id = int(message.command[1])
        except ValueError:
            return await message.reply("❌ ID tidak valid.")
    else:
        return await message.reply("❗ Balas pesan pengguna atau kirim `/riwayat user_id`.")

    async with aiosqlite.connect("history.db") as db:
        async with db.execute("""
            SELECT first_name, last_name, username, timestamp FROM history
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, (target_id,)) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return await message.reply("❌ Tidak ada riwayat yang ditemukan.")

    text = f"📜 **Riwayat Identitas untuk** `{target_id}`:\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n"

    for i, (first, last, uname, time) in enumerate(rows, start=1):
        name = f"{first or ''} {last or ''}".strip()
        username = f"@{uname}" if uname else "❌ Tidak ada"
        text += f"**{i}.** {name} | {username}\n🕒 `{time}`\n\n"

    await message.reply(text)

# Perintah /cari: cari riwayat berdasarkan username
@app.on_message(filters.command("cari") & (filters.group | filters.private))
async def search_by_username(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❗ Gunakan format `/cari username` (tanpa @).")

    username = message.command[1].lstrip("@").lower()

    async with aiosqlite.connect("history.db") as db:
        async with db.execute("""
            SELECT user_id, first_name, last_name, username, timestamp FROM history
            WHERE LOWER(username) = ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, (username,)) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return await message.reply("❌ Tidak ditemukan riwayat untuk username itu.")

    text = f"🔍 **Hasil pencarian untuk** `@{username}`:\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n"

    for i, (uid, first, last, uname, time) in enumerate(rows, start=1):
        name = f"{first or ''} {last or ''}".strip()
        uname_fmt = f"@{uname}" if uname else "❌ Tidak ada"
        text += f"**{i}.** {name} (`{uid}`)\n🏷️ {uname_fmt}\n🕒 `{time}`\n\n"

    await message.reply(text)

# Jalankan bot
if __name__ == "__main__":
    logging.info("✅ Memulai bot SangMata Clone...")
    asyncio.get_event_loop().run_until_complete(init_db())
    app.run()
