import os
import logging
import threading
from flask import Flask
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# load env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MONGO_URL = os.getenv("MONGO_URL")
CHANNEL_URL = os.getenv("CHANNEL_URL", "")
SUPPORT_GROUP_URL = os.getenv("SUPPORT_GROUP_URL", "")

# mongo setup
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["GUARDIAN"]
users_col = db["users"]
groups_col = db["groups"]

# flask setup
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "🟢 edit guardian bot is running successfully"

# logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─────────────────────────────
# start command
# ─────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    bot_username = (await bot.get_me()).username
    user = update.effective_user
    chat = update.effective_chat

    if chat.type == "private":
        users_col.update_one({"_id": user.id}, {"$set": {"name": user.full_name}}, upsert=True)
    elif chat.type in ["group", "supergroup"]:
        groups_col.update_one({"_id": chat.id}, {"$set": {"title": chat.title}}, upsert=True)

    keyboard = [
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ɢʀᴏᴜᴘ", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("📢 ᴄʜᴀɴɴᴇʟ", url=CHANNEL_URL)],
        [InlineKeyboardButton("💬 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=SUPPORT_GROUP_URL)],
        [InlineKeyboardButton("ℹ️ ʜᴇʟᴘ", callback_data="help")]
    ]

    text = (
        "✨ <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴇᴅɪᴛ ɢᴜᴀʀᴅɪᴀɴ ʙᴏᴛ</b> ✨\n\n"
        "🔹 ᴛʜɪs ʙᴏᴛ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ <b>ᴅᴇʟᴇᴛᴇs ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇs</b> ɪɴ ɢʀᴏᴜᴘs.\n"
        "🔹 ʜᴇʟᴘs ᴍᴀɪɴᴛᴀɪɴ ᴛʀᴀɴsᴘᴀʀᴇɴᴄʏ ɪɴ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴs.\n\n"
        "✅ ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ & ɢɪᴠᴇ <b>ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs</b> ᴘᴇʀᴍɪssɪᴏɴ."
    )

    await update.message.reply_html(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ─────────────────────────────
# help menu
# ─────────────────────────────
async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        text = (
            "⚙️ <b>ʜᴇʟᴘ ᴍᴇɴᴜ</b>\n\n"
            "🔹 <b>ᴍᴇssᴀɢᴇ ɢᴜᴀʀᴅɪᴀɴ:</b> ɪғ sᴏᴍᴇᴏɴᴇ ᴇᴅɪᴛs ᴀ ᴍᴇssᴀɢᴇ ɪɴ ɢʀᴏᴜᴘ, ʙᴏᴛ ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ ɪᴛ.\n"
            "🔹 <b>ʙʀᴏᴀᴅᴄᴀsᴛ:</b> ᴏɴʟʏ ᴀᴅᴍɪɴ ᴄᴀɴ sᴇɴᴅ ᴍᴇssᴀɢᴇs ᴛᴏ ᴀʟʟ ᴜsᴇʀs & ɢʀᴏᴜᴘs.\n\n"
            "✅ ᴍᴀᴋᴇ sᴜʀᴇ ʙᴏᴛ ʜᴀs <b>ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇ</b> ʀɪɢʜᴛs ɪɴ ɢʀᴏᴜᴘs."
        )
        await query.edit_message_text(text, parse_mode="HTML")

# ─────────────────────────────
# edited message handler
# ─────────────────────────────
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

# ─────────────────────────────
# broadcast command
# ─────────────────────────────
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CURRENT_ADMIN_ID = 7804972365 
    user_id = update.effective_user.id

    if user_id not in [ADMIN_ID, CURRENT_ADMIN_ID]:
        return await update.message.reply_text("❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")

    if not context.args:
        return await update.message.reply_text("ᴜsᴀɢᴇ: /broadcast <ᴍᴇssᴀɢᴇ>")

    text = " ".join(context.args)
    sent_count = 0
    failed_count = 0

    for user in users_col.find():
        try:
            await context.bot.send_message(chat_id=user["_id"], text=text)
            sent_count += 1
        except Exception as e:
            failed_count += 1
            logger.warning(f"Failed to send to user {user['_id']}: {e}")

    for group in groups_col.find():
        try:
            await context.bot.send_message(chat_id=group["_id"], text=text)
            sent_count += 1
        except Exception as e:
            failed_count += 1
            logger.warning(f"Failed to send to group {group['_id']}: {e}")

    await update.message.reply_text(f"✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ.\n\nsᴇɴᴛ: {sent_count}\nғᴀɪʟᴇᴅ: {failed_count}")

# ─────────────────────────────
# run bot
# ─────────────────────────────
def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(help_menu, pattern="help"))
    application.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE, edited_message_handler))
    application.add_handler(CommandHandler("broadcast", broadcast))

    logger.info("edit guardian bot started 🚀")
    application.run_polling(drop_pending_updates=True)

# ─────────────────────────────
# main
# ─────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
