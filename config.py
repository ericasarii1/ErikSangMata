import sqlite3
from pyrogram import Client, filters
from pyrogram.types import Message

# Konfigurasi bot
API_ID = 12345678  # Ganti dengan API ID kamu
API_HASH = "your_api_hash_here"
BOT_TOKEN = "your_bot_token_here"
LOG_CHANNEL = -1001234567890  # Opsional, ganti dengan channel log jika perlu

# Inisialisasi database
conn = sqlite3.connect("sangmata.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS identity_history (
    user_id INTEGER,
    name TEXT,
    username TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# Fungsi untuk menyimpan identitas dan cek perubahan
def save_identity(user_id: int, name: str, username: str):
    cur.execute("SELECT name, username FROM identity_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
    row = cur.fetchone()
    if row is None or row[0] != name or row[1] != username:
        cur.execute("INSERT INTO identity_history (user_id, name, username) VALUES (?, ?, ?)", (user_id, name, username))
        conn.commit()
        return row
    return None

# Inisialisasi bot
bot = Client("sangmata_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Tracking otomatis nama/username di grup
@bot.on_message(filters.group & filters.text)
async def track_identity(_, msg: Message):
    user = msg.from_user
    if not user or user.is_bot:
        return

    old_data = save_identity(user.id, user.first_name, user.username or "")
    if old_data:
        if old_data[0] != user.first_name:
            await msg.reply_text(f"User {user.id} changed name from {old_data[0]} to {user.first_name}")
        if old_data[1] != (user.username or ""):
            await msg.reply_text(f"User {user.id} changed username from {old_data[1]} to {user.username}")

# Perintah /riwayat via reply
@bot.on_message(filters.command("riwayat") & filters.reply)
async def riwayat(_, msg: Message):
    user = msg.reply_to_message.from_user
    if not user:
        return await msg.reply_text("Tidak dapat menemukan pengguna.")

    cur.execute("SELECT name, username, timestamp FROM identity_history WHERE user_id = ? ORDER BY timestamp DESC", (user.id,))
    rows = cur.fetchall()
    if not rows:
        return await msg.reply_text("Tidak ada riwayat untuk pengguna ini.")

    teks = f"Riwayat nama/username untuk {user.first_name} [ID: {user.id}]:\n"
    for name, username, time in rows:
        teks += f"- {time}: {name} | @{username if username else '—'}\n"

    await msg.reply_text(teks)

bot.run()
