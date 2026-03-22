import json
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
except ValueError:
    raise ValueError("ADMIN_ID має бути числом")

if not TOKEN:
    raise ValueError("ENV TOKEN не заданий")

if ADMIN_ID == 0:
    raise ValueError("ENV ADMIN_ID не заданий або = 0")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE_DIR, "data.json")

user_states = {}
user_data = {}

services = {
    "чистка зубів": "500 грн",
    "відбілювання": "1500 грн",
    "брекети": "12000 грн",
    "ретейнери": "2000 грн",
    "карієс": "800 грн",
    "пломба": "700 грн",
    "видалення зуба": "1000 грн",
    "інше": "уточнюється"
}

# --- JSON ---
def load_data():
    if not os.path.exists(FILE):
        return {"clients": [], "times": ["10:00", "11:00", "13:00"]}
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- keyboards ---
def menu_kb():
    return ReplyKeyboardMarkup(
        [["ціни", "запис"], ["консультація"]],
        resize_keyboard=True
    )

def services_kb():
    return ReplyKeyboardMarkup(
        [[s] for s in services.keys()],
        resize_keyboard=True
    )

def times_kb(times):
    return ReplyKeyboardMarkup(
        [[t] for t in times],
        resize_keyboard=True
    )

def phone_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Поділитися номером", request_contact=True)]],
        resize_keyboard=True
    )

def back_kb():
    return ReplyKeyboardMarkup(
        [["меню"]],
        resize_keyboard=True
    )

# --- start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_states[update.message.from_user.id] = "menu"
    await update.message.reply_text(
        "👋 Вітаємо!\nОберіть, що вас цікавить:",
        reply_markup=menu_kb()
    )

# --- handler ---
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    data = load_data()

    if user_id not in user_states:
        user_states[user_id] = "menu"

    state = user_states[user_id]

    # 🔥 CONTACT
    if update.message.contact:
        if state == "phone":
            user_data[user_id]["phone"] = update.message.contact.phone_number

            client = user_data[user_id]

            if not all(k in client for k in ("name", "service", "time", "phone")):
                await update.message.reply_text("❌ Помилка, почніть знову", reply_markup=menu_kb())
                user_states[user_id] = "menu"
                return

            data["clients"].append(client)

            if client["time"] in data["times"]:
                data["times"].remove(client["time"])

            save_data(data)

            # 🔔 адміну
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🆕 КЛІЄНТ\n\n"
                     f"👤 {client['name']}\n"
                     f"📞 {client['phone']}\n"
                     f"📌 {client['service']}\n"
                     f"⏰ {client['time']}"
            )

            await update.message.reply_text(
                f"✅ Запис підтверджено!\n\n"
                f"{client['service']} о {client['time']}\n"
                f"Ми вам зателефонуємо 📞",
                reply_markup=menu_kb()
            )

            user_states[user_id] = "menu"
            user_data[user_id] = {}
        return

    text = update.message.text.lower() if update.message.text else ""

    # --- MENU ---
    if text == "меню":
        user_states[user_id] = "menu"
        await update.message.reply_text("Оберіть:", reply_markup=menu_kb())
        return

    # --- ЦІНИ ---
    if text == "ціни":
        user_states[user_id] = "price"
        await update.message.reply_text("💰 Оберіть послугу:", reply_markup=services_kb())
        return

    if state == "price":
        if text in services:
            await update.message.reply_text(
                f"{text} — {services[text]}",
                reply_markup=menu_kb()
            )
        else:
            await update.message.reply_text("❗ Оберіть кнопку")
        return

    # --- ЗАПИС ---
    if text == "запис":
        user_states[user_id] = "service"
        await update.message.reply_text("📅 Оберіть послугу:", reply_markup=services_kb())
        return

    if state == "service":
        if text not in services:
            await update.message.reply_text("❗ Оберіть кнопку")
            return

        user_data[user_id] = {"service": text}

        if text == "інше":
            user_states[user_id] = "custom_service"
            await update.message.reply_text("✍️ Опишіть проблему:")
            return

        user_states[user_id] = "time"

        if not data["times"]:
            await update.message.reply_text("❌ Немає вільних слотів", reply_markup=menu_kb())
            user_states[user_id] = "menu"
            return

        await update.message.reply_text("⏰ Оберіть час:", reply_markup=times_kb(data["times"]))
        return

    if state == "custom_service":
        user_data[user_id]["service"] = text
        user_states[user_id] = "time"

        await update.message.reply_text("⏰ Оберіть час:", reply_markup=times_kb(data["times"]))
        return

    if state == "time":
        if text not in data["times"]:
            await update.message.reply_text("❗ Оберіть час кнопкою")
            return

        user_data[user_id]["time"] = text
        user_states[user_id] = "name"

        await update.message.reply_text("👤 Як вас звати?")
        return

    if state == "name":
        if len(text) < 2:
            await update.message.reply_text("❗ Введіть нормальне ім’я")
            return

        user_data[user_id]["name"] = text
        user_states[user_id] = "phone"

        await update.message.reply_text(
            "📱 Поділіться номером:",
            reply_markup=phone_kb()
        )
        return

    # --- КОНСУЛЬТАЦІЯ ---
    if text == "консультація":
        await update.message.reply_text(
            "📞 Ми вам передзвонимо найближчим часом",
            reply_markup=menu_kb()
        )
        return

    # --- fallback ---
    await update.message.reply_text("Оберіть кнопку 👇", reply_markup=menu_kb())


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("🔥 MAX BOT READY")

    app.run_polling()

if __name__ == "__main__":
    main()