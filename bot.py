import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import config

WARN_FILE = 'warnings.json'
WARN_LIMIT = 3
MUTE_DURATION = 3600  # 1 hour in seconds

def get_inline_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{config.BOT_TOKEN.split(':')[0]}?startgroup=true")],
        [InlineKeyboardButton("👤 Founder", url=config.FOUNDER_URL)],
        [InlineKeyboardButton("💬 Support Group", url=config.SUPPORT_URL)]
    ]
    return InlineKeyboardMarkup(keyboard)

def load_warnings():
    try:
        with open(WARN_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_warnings(data):
    with open(WARN_FILE, 'w') as f:
        json.dump(data, f)

async def check_bio_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = msg.from_user
    uid = str(user.id)

    if user.id in config.ADMIN_IDS:
        return

    text = msg.text.lower()
    if any(link in text for link in config.BIO_LINKS):
        try:
            await msg.delete()
        except:
            pass

        warnings = load_warnings()
        warnings.setdefault(uid, 0)
        warnings[uid] += 1
        save_warnings(warnings)

        warn_count = warnings[uid]
        reply_text = f"🚫 @{user.username or user.first_name}, bio links are not allowed. Warning {warn_count}/{WARN_LIMIT}."
        await context.bot.send_message(chat_id=msg.chat_id, text=reply_text, reply_markup=get_inline_keyboard())

        if warn_count >= WARN_LIMIT:
            try:
                await context.bot.restrict_chat_member(chat_id=msg.chat_id, user_id=user.id,
                                                       permissions=update.effective_chat.default_permissions,
                                                       until_date=int(update.message.date.timestamp()) + MUTE_DURATION)
                await context.bot.send_message(msg.chat_id,
                                               f"🔇 @{user.username or user.first_name} has been muted for {MUTE_DURATION//60} minutes (3 warnings).")
                warnings[uid] = 0
                save_warnings(warnings)
            except Exception as e:
                print("Mute failed:", e)

async def run_bot():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_bio_links))
    print("🤖 Bot is running…")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run_bot())
