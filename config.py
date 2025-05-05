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

# Load environment variables
load_dotenv()

api_id = int(os.getenv("API_ID", ""))
api_hash = os.getenv("API_HASH", "")
bot_token = os.getenv("BOT_TOKEN", "")
log_channel = int(os.getenv("LOG_CHANNEL", ""))

app = Client("sangmata_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Sudo/admin/support list
SUDO_USERS = [7742582171, 7697902976]  # Ganti dengan ID asli Anda

def is_sudo(user_id):
    return user_id in SUDO_USERS

def is_admin_check():
    async def func(_, __, message):
        if message.chat.type == "private":
            return is_sudo(message.from_user.id)
        member = await message.chat.get_member(message.from_user.id)
        return member.status in ("administrator", "creator") or is_sudo(message.from_user.id)
    return filters.create(func)

# Database init
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

# Save history
async def save_history(uid, first_name, last_name, username):
    async with aiosqlite.connect("history.db") as db:
        await db.execute("""
            INSERT INTO history (user_id, first_name, last_name, username)
            VALUES (?, ?, ?, ?)
        """, (uid, first_name, last_name, username))
        await db.commit()

# /riwayat command
@app.on_message(filters.command("riwayat") & (filters.group | filters.private))
async def riwayat_handler(client: Client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            target_id = int(message.command[1])
        except ValueError:
            return await message.reply("❌ ID tidak valid.")
    else:
        return await message.reply("❗ Balas pesan atau gunakan `/riwayat user_id`.")

    async with aiosqlite.connect("history.db") as db:
        async with db.execute("""
            SELECT first_name, last_name, username, timestamp FROM history
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (target_id,)) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return await message.reply("❌ Tidak ada riwayat ditemukan.")

    text = f"📜 **Riwayat Identitas untuk** `{target_id}`:\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, (first, last, uname, time) in enumerate(rows, start=1):
        name = f"{first or ''} {last or ''}".strip()
        username = f"@{uname}" if uname else "❌ Tidak ada"
        text += f"**{i}.** {name} | {username}\n🕒 `{time}`\n\n"

    await message.reply(text)

# /search command
@app.on_message(filters.command("search") & (filters.group | filters.private))
async def search_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❗ Gunakan `/search keyword` untuk mencari nama atau username.")
    keyword = message.text.split(None, 1)[1]

    async with aiosqlite.connect("history.db") as db:
        async with db.execute("""
            SELECT user_id, first_name, last_name, username, timestamp FROM history
            WHERE first_name LIKE ? OR last_name LIKE ? OR username LIKE ?
            ORDER BY timestamp DESC LIMIT 20
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return await message.reply("❌ Tidak ada hasil ditemukan.")

    text = f"🔎 **Hasil pencarian untuk:** `{keyword}`\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, (uid, first, last, uname, time) in enumerate(rows, start=1):
        name = f"{first or ''} {last or ''}".strip()
        username = f"@{uname}" if uname else "❌"
        text += f"**{i}.** `{uid}`\n👤 {name} | {username}\n🕒 `{time}`\n\n"

    await message.reply(text)

# /hapus_riwayat command
@app.on_message(filters.command("hapus_riwayat") & is_admin_check())
async def hapus_riwayat_handler(client: Client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            target_id = int(message.command[1])
        except ValueError:
            return await message.reply("❌ ID tidak valid.")
    else:
        return await message.reply("❗ Gunakan `/hapus_riwayat user_id` atau balas pesan.")

    async with aiosqlite.connect("history.db") as db:
        await db.execute("DELETE FROM history WHERE user_id = ?", (target_id,))
        await db.commit()

    await message.reply(f"✅ Riwayat untuk `{target_id}` berhasil dihapus.")

# /id command
@app.on_message(filters.command("id") & (filters.group | filters.private))
async def id_handler(client: Client, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await client.get_users(int(message.command[1]))
        except Exception:
            return await message.reply("❌ Tidak bisa mendapatkan informasi pengguna.")
    else:
        return await message.reply("❗ Gunakan `/id user_id` atau balas pesan.")

    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "❌ Tidak ada"
    await message.reply(f"🧾 **ID Pengguna**\n👤 Nama: {name}\n🏷️ Username: {username}\n🆔 ID: `{user.id}`")

# /nama command
@app.on_message(filters.command("nama") & (filters.group | filters.private))
async def nama_handler(client: Client, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await client.get_users(int(message.command[1]))
        except Exception:
            return await message.reply("❌ Tidak bisa mendapatkan pengguna.")
    else:
        return await message.reply("❗ Gunakan `/nama user_id` atau balas pesan.")

    name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    await message.reply(f"👤 **Nama Pengguna**: {name}")

# /username command
@app.on_message(filters.command("username") & (filters.group | filters.private))
async def username_handler(client: Client, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            user = await client.get_users(int(message.command[1]))
        except Exception:
            return await message.reply("❌ Tidak bisa mendapatkan pengguna.")
    else:
        return await message.reply("❗ Gunakan `/username user_id` atau balas pesan.")

    username = f"@{user.username}" if user.username else "❌ Tidak ada username"
    await message.reply(f"🏷️ **Username**: {username}")

# Track identity changes
@app.on_message(filters.group | filters.private)
async def track_user(client: Client, message: Message):
    user = message.from_user
    if not user or user.is_bot:
        return

    uid = user.id
    first = user.first_name or ""
    last = user.last_name or ""
    uname = user.username or ""

    async with aiosqlite.connect("history.db") as db:
        async with db.execute("""
            SELECT first_name, last_name, username FROM history
            WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (uid,)) as cursor:
            row = await cursor.fetchone()

    old_first, old_last, old_uname = row if row else ("", "", "")
    if (first, last, uname) != (old_first, old_last, old_uname):
        display_name = f"{old_first or first}".strip()
        text = (
            f"⚠️ **Perubahan Deteksi Identitas!**\n"
            f"👤 {display_name} (`{uid}`)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 **Nama Lama:** {old_first} {old_last}\n"
            f"🔖 **Username Lama:** @{old_uname if old_uname else 'Tidak Ada'}\n"
            f"🆕 **Nama Baru:** {first} {last}\n"
            f"🏷️ **Username Baru:** @{uname if uname else 'Tidak Ada'}"
        )
        try:
            await message.reply(text)
        except:
            pass
        if log_channel != 0:
            try:
                await client.send_message(log_channel, text)
            except Exception as e:
                logging.warning(f"Gagal kirim ke log channel: {e}")

    await save_history(uid, first, last, uname)

# Run bot
if __name__ == "__main__":
    logging.info("✅ Memulai bot...")
    asyncio.get_event_loop().run_until_complete(init_db())
    app.run()
