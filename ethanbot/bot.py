from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext,
    ChatMemberHandler, filters
)
from datetime import datetime
from dotenv import load_dotenv
import os

# Muat token dan ID Telegram dari file .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Ganti dengan ID Telegram kamu

if TOKEN is None or ADMIN_ID is None:
    print("Token atau ID admin tidak ditemukan. Pastikan file .env sudah benar.")
    exit(1)

# Variabel untuk menyimpan statistik admin
stats = {
    "admin_online": 0,
    "messages_deleted": 0,
    "admin_replies": 0
}

# Callback untuk mengirim laporan statistik ke chat pribadi admin
async def send_private_stats(context: CallbackContext):
    message = (
        f"📊 **Laporan Statistik Admin**:\n"
        f"- Admin Online Saat Ini: {stats['admin_online']}\n"
        f"- Pesan Dihapus oleh Admin: {stats['messages_deleted']}\n"
        f"- Pesan Direply Admin: {stats['admin_replies']}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)

# Callback untuk command /laporan
async def laporan(update: Update, context: CallbackContext):
    if update.effective_chat.id == ADMIN_ID:
        await send_private_stats(context)
    else:
        await update.message.reply_text("Laporan hanya bisa diakses oleh admin melalui chat pribadi.")

# Callback untuk memantau admin online/offline
async def monitor_admin(update: ChatMemberUpdated, context: CallbackContext):
    new_status = update.chat_member.new_chat_member.status
    if new_status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        stats["admin_online"] += 1
    else:
        stats["admin_online"] = max(0, stats["admin_online"] - 1)
    await send_private_stats(context)

# Callback untuk mendeteksi pesan yang di-reply oleh admin
async def detect_reply(update: Update, context: CallbackContext):
    if update.message.reply_to_message and update.message.from_user.id in context.bot_data.get("admins", []):
        stats["admin_replies"] += 1
        await send_private_stats(context)

# Simpan pesan yang dikirim agar bisa dibandingkan jika ada yang terhapus
messages_log = {}

# Callback untuk mencatat pesan baru
async def log_message(update: Update, context: CallbackContext):
    messages_log[update.message.message_id] = update.message

# Callback untuk mendeteksi pesan yang dihapus
async def detect_deleted_message(update: Update, context: CallbackContext):
    message_id = update.effective_message.message_id
    if message_id in messages_log:
        del messages_log[message_id]
        stats["messages_deleted"] += 1
        await send_private_stats(context)

# Callback untuk /start di grup dan chat pribadi
async def start(update: Update, context: CallbackContext):
    chat_type = update.message.chat.type
    if chat_type == "private":
        await update.message.reply_text("Halo! Saya adalah bot pemantau untuk grup Anda.")
    elif chat_type in ["group", "supergroup"]:
        await update.message.reply_text("Halo grup! Saya sekarang memantau aktivitas admin di sini.")
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        context.bot_data["admins"] = [admin.user.id for admin in admins]

# Inisialisasi bot
app = ApplicationBuilder().token(TOKEN).build()

# Daftar handler
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("laporan", laporan))  # Tambahkan handler untuk /laporan
app.add_handler(ChatMemberHandler(monitor_admin, ChatMemberHandler.MY_CHAT_MEMBER))
app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.NEW_CHAT_MEMBERS, log_message))
app.add_handler(MessageHandler(filters.REPLY, detect_reply))

print("Bot berjalan...")
app.run_polling()
