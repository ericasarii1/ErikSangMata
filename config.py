import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Load .env jika ada
load_dotenv()

# Konfigurasi
api_id = int(os.getenv("API_ID", "23746013"))
api_hash = os.getenv("API_HASH", "c4c86f53aac9b29f7fa28d5ba953be44")
bot_token = os.getenv("BOT_TOKEN", "8075975593:AAGwlvtF4usR5x6rn-dAYsveuZtmWSZAKT8")

app = Client(
    "sangmata_bot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token
)

# Penyimpanan sementara nama & username
usernames = {}

@app.on_message(filters.group)
async def track_user(client: Client, message: Message):
    user = message.from_user
    if not user or user.is_bot:
        return

    current = (user.first_name or "", user.last_name or "", user.username or "")
    old = usernames.get(user.id)

    if old and old != current:
        old_name = f"{old[0]} {old[1]}".strip()
        new_name = f"{current[0]} {current[1]}".strip()
        old_username = f"@{old[2]}" if old[2] else "Tidak ada"
        new_username = f"@{current[2]}" if current[2] else "Tidak ada"

        await message.reply(
            f"**Perubahan terdeteksi!**\n"
            f"👤 [{user.first_name}](tg://user?id={user.id}) (`{user.id}`)\n\n"
            f"**Nama Sebelumnya:** {old_name}\n"
            f"**Username Sebelumnya:** {old_username}\n\n"
            f"**Nama Sekarang:** {new_name}\n"
            f"**Username Sekarang:** {new_username}"
        )

    usernames[user.id] = current

if __name__ == "__main__":
    logging.info("Bot SangMata versi keren sedang berjalan...")
    app.run()
