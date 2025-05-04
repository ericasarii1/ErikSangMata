import os, logging, asyncio, aiosqlite
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

load_dotenv()

api_id = int(os.getenv("API_ID", ""))
api_hash = os.getenv("API_HASH", "")
bot_token = os.getenv("BOT_TOKEN", "")
log_channel = int(os.getenv("LOG_CHANNEL_ID", ""))

app = Client("sangmata_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
usernames = {}

# Inisialisasi Database
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

# Simpan ke database
async def save_history(uid, first_name, last_name, username):
    async with aiosqlite.connect("history.db") as db:
        await db.execute("""
            INSERT INTO history (user_id, first_name, last_name, username)
            VALUES (?, ?, ?, ?)
        """, (uid, first_name, last_name, username))
        await db.commit()

# Ambil riwayat dari database
async def get_history(uid):
    async with aiosqlite.connect("history.db") as db:
        cursor = await db.execute("""
            SELECT first_name, last_name, username, timestamp
            FROM history
            WHERE user_id = ?
            ORDER BY timestamp
        """, (uid,))
        return await cursor.fetchall()

@app.on_message(filters.group)
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
            f"👤 [{user.first_name}](tg://user?id={uid}) (`{uid}`)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 **Nama Lama:** `{old_name}`\n"
            f"🔖 **Username Lama:** `{old_username}`\n"
            f"🆕 **Nama Baru:** `{new_name}`\n"
            f"🏷️ **Username Baru:** `{new_username}`"
        )

        await message.reply(text)
        await client.send_message(log_channel, text)

        # Simpan riwayat ke database
        await save_history(uid, old[0], old[1], old[2])

    usernames[uid] = current

@app.on_message(filters.command("riwayat") & filters.private)
async def check_history(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Format salah!\nKirim: `/riwayat <user_id>`", quote=True)

    try:
        uid = int(args[1])
        history = await get_history(uid)

        if not history:
            return await message.reply("Tidak ada riwayat ditemukan.")

        lines = []
        for idx, (first, last, username, ts) in enumerate(history, 1):
            name = f"{first} {last}".strip()
            uname = f"@{username}" if username else "❌ Tidak ada"
            lines.append(f"{idx}. `{name}` | `{uname}` | `{ts}`")

        await message.reply("📜 Riwayat perubahan:\n" + "\n".join(lines))

    except Exception as e:
        await message.reply(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    logging.info("🚀 Memulai SangMata Bot dengan SQLite logging...")
    asyncio.get_event_loop().run_until_complete(init_db())
    app.run()
