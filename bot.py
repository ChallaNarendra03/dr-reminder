import os
import logging
import sqlite3
from datetime import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    gender TEXT
)
""")
conn.commit()

# ---------------- DAILY SCHEDULE ----------------
SCHEDULE = [
    (6, 0, "🌅 Good Morning! Have a great day!"),
    (8, 0, "🥣 Don't forget to eat breakfast!"),
    (10, 0, "💧 Drink some water! Stay hydrated!"),
    (13, 0, "🍛 Don't skip lunch!"),
    (17, 30, "🌆 How is your day going?"),
    (20, 30, "🍽 Go and eat dinner!"),
    (23, 0, "🌙 It's time to sleep. Good night ❤️ I miss you"),
]

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Male", "Female"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "Please select your gender:",
        reply_markup=reply_markup,
    )

# ---------------- GENDER SELECTION ----------------
async def handle_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    gender = update.message.text.lower()

    if gender not in ["male", "female"]:
        return

    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (chat_id, gender))
    conn.commit()

    if gender == "male":
        welcome = "😎 Welcome Mawa Broh! Daily Care Activated 💙"
    else:
        welcome = "❤️ Welcome Honey! Daily Care Activated 💖"

    await update.message.reply_text(welcome)

    # Schedule messages
    for hour, minute, message in SCHEDULE:
        context.job_queue.run_daily(
            send_scheduled_message,
            time=time(hour, minute),
            chat_id=chat_id,
            data=message,
        )

# ---------------- SCHEDULE MESSAGE ----------------
async def send_scheduled_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id

    cursor.execute("SELECT gender FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()

    if not result:
        return

    gender = result[0]
    message = context.job.data

    if gender == "male":
        message = f"Mawa Bro 😎 {message}"
    else:
        message = f"Hey Honey ❤️ {message}"

    await context.bot.send_message(chat_id=chat_id, text=message)

# ---------------- FRIENDLY REPLY ----------------
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text.lower()

    cursor.execute("SELECT gender FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()

    if not result:
        await update.message.reply_text("Please type /start first ❤️")
        return

    gender = result[0]

    # Friendly intelligent replies
    if "hi" in user_text or "hello" in user_text:
        reply = "Heyyy! I'm always here for you 💛"
    elif "how are you" in user_text:
        reply = "I'm good because you're here 😊 What about you?"
    elif "sad" in user_text or "depressed" in user_text:
        reply = "Don't worry... I'm with you ❤️ Tell me what happened."
    elif "love" in user_text:
        reply = "Awww 💖 I care about you so much!"
    elif "problem" in user_text:
        reply = "Tell me everything. We'll solve it together 💪"
    else:
        reply = "I'm listening 👀 Tell me more..."

    if gender == "male":
        reply = f"Mawa Bro 😎 {reply}"
    else:
        reply = f"Hey Honey ❤️ {reply}"

    await update.message.reply_text(reply)

# ---------------- MAIN ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Regex("^(Male|Female)$"), handle_gender))
app.add_handler(MessageHandler(filters.TEXT & ~filters.Regex("^(Male|Female)$"), handle_user_message))

app.run_polling()
