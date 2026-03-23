import os
import psycopg2
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

DATABASE_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True

user_data = {}

# створення таблиць
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name TEXT,
    phone TEXT,
    service TEXT,
    time TEXT
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS times (
    id SERIAL PRIMARY KEY,
    value TEXT
);
""")

# старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_user.id] = {}
    await update.message.reply_text("Привіт! Як вас звати?")

# текст
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if uid not in user_data:
        user_data[uid] = {}

    data = user_data[uid]

    # ім'я
    if "name" not in data:
        data["name"] = text
        btn = KeyboardButton("Поділитися номером", request_contact=True)
        await update.message.reply_text("Поділіться номером:", reply_markup=ReplyKeyboardMarkup([[btn]], resize_keyboard=True))
        return

    # послуга
    if "service" not in data:
        data["service"] = text
        cur = conn.cursor()
        cur.execute("SELECT value FROM times")
        times = [t[0] for t in cur.fetchall()]

        keyboard = [[t] for t in times]
        await update.message.reply_text("Оберіть час:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    # час
    if "time" not in data:
        data["time"] = text
        await update.message.reply_text("Готово. Тепер номер телефону 👇")
        return

# контакт
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    phone = update.message.contact.phone_number

    data = user_data.get(uid, {})
    data["phone"] = phone

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO clients (name, phone, service, time) VALUES (%s,%s,%s,%s)",
        (data.get("name"), phone, data.get("service"), data.get("time"))
    )

    await update.message.reply_text("✅ Запис прийнято! Ми вам зателефонуємо.")

    user_data.pop(uid, None)

# запуск
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.CONTACT, contact))
app.add_handler(MessageHandler(filters.TEXT, handle))

app.run_polling()
