import sqlite3
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Konfigurasi bot
API_ID = 29545467
API_HASH = ""
BOT_TOKEN = ""
LOG_CHANNEL = -100  # Opsional

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

# Handler /start
@bot.on_message(filters.private & filters.command("start"))
async def start(_, msg: Message):
    teks = (
        "Hello! 👋\n\n"
        "**If you're a group admin:**\n"
        "You can add this bot by clicking the button below. Make sure that you add the SangMata bot as **ADMIN** with \"Manage Group\" permission so that it can work properly!\n\n"
        "**If you want to query a user history:**\n"
        "There are 3 ways:\n"
        "1. You can forward the user's message here\n"
        "2. Type and send their ID or username (donator only) in this chat\n"
        "3. Use `/riwayat` (balas pesan pengguna)\n\n"
        "**If you need help:**\n"
        "Just type and send 'help' in the chat or join our support group @Grup_Ovanime_Indo to ask for help."
    )

    tombol = InlineKeyboardMarkup(
        [[InlineKeyboardButton("➕ Add Bot to Group", url="https://t.me/SangMataOvanime_Robot?startgroup=true")]]
    )

    await msg.reply_text(teks, reply_markup=tombol, disable_web_page_preview=True)

# Handler /help
@bot.on_message(filters.private & (filters.regex("^(help|h)$") | filters.command(["help", "h"])))
async def help_message(_, msg: Message):
    teks = (
        "**List of commands**\n\n"
        "**Group Configs:**\n"
        "`getconfig` or `gc` - Get current group config\n"
        "`setconfig` or `sc` - Set config for current group\n"
        "`resetconfig` or `rc` - Reset config to default value for current group\n\n"
        "**Search Commands:**\n"
        "`history` or `hi` - Query a user its names and usernames in current group\n"
        "`allhistory` or `all` - Query a user its names and usernames in all groups\n\n"
        "**Account Info:**\n"
        "`myaccount` or `my` - Show your account information\n"
        "`myhistory` or `me` - Show your account history\n\n"
        "**Chat Info:**\n"
        "`chatinfo` or `ci` - Show current chat (channel or group) information\n\n"
        "**Other Commands:**\n"
        "`donate` or `d` - Donate to Sang group\n"
        "`groupdonate` or `gd` - Donate as group to Sang group\n"
        "`donatealt` or `da` - Alternative method for donation\n"
        "`version` or `v` - Show bot version\n"
        "`versionhistory` or `vh` - Show bot version and changes log\n"
        "`help` or `h` - Show this help\n\n"
        "**Note:**\n"
        "- In bot private chat, you can send only user/group/channel ID or @username and it will show its history similar to `allhistory` command.\n\n"
        "Visit [this example](https://t.me/Grup_Ovanime_Indo/405)\n"
        "Or ask questions or feedback in @Grup_Ovanime_Indo"
    )
    await msg.reply_text(teks, disable_web_page_preview=True)

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

        # Kirim log ke channel jika LOG_CHANNEL di-set
        if LOG_CHANNEL != -100:
            try:
                await bot.send_message(
                    chat_id=LOG_CHANNEL,
                    text=f"User {user.id} updated identity:\nName: {old_data[0]} -> {user.first_name}\nUsername: {old_data[1]} -> {user.username or '—'}"
                )
            except Exception as e:
                print(f"Gagal mengirim log: {e}")

# Deteksi ID atau username di chat pribadi
@bot.on_message(filters.private & filters.text & ~filters.command(["start", "help"]))
async def handle_id_or_username(_, msg: Message):
    text = msg.text.strip()

    # Coba parse sebagai ID
    if text.isdigit():
        user_id = int(text)
    elif text.startswith("@"):
        # Ambil user info dari username
        try:
            user = await bot.get_users(text)
            user_id = user.id
        except Exception:
            return await msg.reply_text("Username tidak ditemukan.")
    else:
        return await msg.reply_text("Mohon kirim ID numerik atau username diawali '@'.")

    # Ambil riwayat dari database
    cur.execute("SELECT name, username, timestamp FROM identity_history WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    rows = cur.fetchall()
    if not rows:
        return await msg.reply_text("Tidak ada riwayat untuk pengguna ini.")

    teks = f"Riwayat nama/username untuk ID {user_id}:\n"
    for name, username, time in rows:
        teks += f"- {time}: {name} | @{username if username else '—'}\n"

    await msg.reply_text(teks)

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
