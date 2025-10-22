import os
import logging
import threading
from flask import Flask
from pymongo import MongoClient
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.helpers import mention_html
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)
from dotenv import load_dotenv

# ───────────────────────────────────────────────
# Load environment variables
# ───────────────────────────────────────────────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MONGO_URL = os.getenv("MONGO_URL")
CHANNEL_URL = os.getenv("CHANNEL_URL")
SUPPORT_GROUP_URL = os.getenv("SUPPORT_GROUP_URL")

# ───────────────────────────────────────────────
# MongoDB setup
# ───────────────────────────────────────────────
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["NYCREATION"]
users_col = db["users"]
groups_col = db["groups"]

# ───────────────────────────────────────────────
# Logging setup
# ───────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("edit_guardian_bot")

# ───────────────────────────────────────────────
# Telegram Bot Handlers
# ───────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    bot_username = (await context.bot.get_me()).username

    if chat.type == "private":
        users_col.update_one({"_id": user.id}, {"$set": {"name": user.full_name}}, upsert=True)
    elif chat.type in ["group", "supergroup"]:
        groups_col.update_one({"_id": chat.id}, {"$set": {"title": chat.title}}, upsert=True)

    keyboard = [
    [InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", url=f"https://t.me/{bot_username}?startgroup=true")],
    [
        InlineKeyboardButton("📢 ᴄʜᴀɴɴᴇʟ", url=CHANNEL_URL),
        InlineKeyboardButton("💬 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=SUPPORT_GROUP_URL)
    ],
    [InlineKeyboardButton("ℹ️ ʜᴇʟᴘ", callback_data="help")]
]

    text = (
        "✨ <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴇᴅɪᴛ ɢᴜᴀʀᴅɪᴀɴ ʙᴏᴛ</b> ✨\n\n"
        "🔹 ᴛʜɪs ʙᴏᴛ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ <b>ᴅᴇʟᴇᴛᴇs ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇs</b> ɪɴ ɢʀᴏᴜᴘs.\n"
        "🔹 ʜᴇʟᴘs ᴍᴀɪɴᴛᴀɪɴ ᴛʀᴀɴsᴘᴀʀᴇɴᴄʏ ɪɴ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴs.\n\n"
        "✅ ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ & ɢɪᴠᴇ <b>ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs</b> ᴘᴇʀᴍɪssɪᴏɴ."
    )

    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        text = (
            "⚙️ <b>ʜᴇʟᴘ ᴍᴇɴᴜ</b>\n\n"
            "🔹 <b>ᴍᴇssᴀɢᴇ ɢᴜᴀʀᴅɪᴀɴ:</b> ɪғ sᴏᴍᴇᴏɴᴇ ᴇᴅɪᴛs ᴀ ᴍᴇssᴀɢᴇ ɪɴ ɢʀᴏᴜᴘ, ʙᴏᴛ ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ ɪᴛ.\n"
            "🔹 <b>ʙʀᴏᴀᴅᴄᴀsᴛ:</b> ᴏɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇs ᴛᴏ ᴀʟʟ ᴜsᴇʀs & ɢʀᴏᴜᴘs.\n\n"
            "✅ ᴍᴀᴋᴇ sᴜʀᴇ ʙᴏᴛ ʜᴀs <b>ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇ</b> ʀɪɢʜᴛs ɪɴ ɢʀᴏᴜᴘs."
        )
        await query.edit_message_text(text, parse_mode="HTML")

async def edited_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.edited_message
    if not message:
        return
    chat = message.chat
    user = message.from_user
    try:
        await message.delete()
        warn_text = f"⚠️ {mention_html(user.id, user.first_name)}, ʏᴏᴜ ᴇᴅɪᴛᴇᴅ ᴀ ᴍᴇssᴀɢᴇ sᴏ ɪᴛ ᴡᴀs ᴅᴇʟᴇᴛᴇᴅ."
        await chat.send_message(warn_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to delete edited message: {e}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CURRENT_ADMIN_ID = 7804972365 
    user_id = update.effective_user.id
    if user_id != ADMIN_ID and user_id != CURRENT_ADMIN_ID:
        return await update.message.reply_text("❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
    if not context.args:
        return await update.message.reply_text("ᴜsᴀɢᴇ: /broadcast <message>")
    text = " ".join(context.args)
    count = 0
    for user in users_col.find():
        try:
            await context.bot.send_message(chat_id=user["_id"], text=text)
            count += 1
        except Exception as e:
            logger.warning(f"Failed to send to user {user['_id']}: {e}")
    for group in groups_col.find():
        try:
            await context.bot.send_message(chat_id=group["_id"], text=text)
            count += 1
        except Exception as e:
            logger.warning(f"Failed to send to group {group['_id']}: {e}")
    await update.message.reply_text(f"✅ ʙʀᴏᴀᴅᴄᴀsᴛ sᴇɴᴛ ᴛᴏ {count} ᴄʜᴀᴛs.")

# ───────────────────────────────────────────────
# Flask Web Server
# ───────────────────────────────────────────────
app = Flask(__name__)

@app.route("/")
def home():
    return "🛡️ ᴇᴅɪᴛ ɢᴜᴀʀᴅɪᴀɴ ʙᴏᴛ ɪs ʀᴜɴɴɪɴɢ!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# ───────────────────────────────────────────────
# Run bot safely without signal issues
# ───────────────────────────────────────────────
def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(help_menu, pattern="help"))
    application.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, edited_message_handler))
    application.add_handler(CommandHandler("broadcast", broadcast))
    logger.info("🟢 edit guardian bot started 🚀")
    application.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
