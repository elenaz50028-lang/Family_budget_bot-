import os
import sqlite3
import telebot
from datetime import datetime
from openai import OpenAI

BOT_TOKEN = os.getenv("8996097304:AAGQ-lwjYYTV7-YAZjEUPFPLWzrXvaO7CHA")
OPENAI_API_KEY = os.getenv("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")

if not BOT_TOKEN:
    raise ValueError("❌ Переменная BOT_TOKEN не задана в Render")

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

DB_FILE = "budget.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, type TEXT, amount REAL,
        description TEXT, date TEXT)""")
    conn.commit()
    conn.close()
init_db()

def add_transaction(user_id, t_type, amount, desc):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO transactions VALUES (NULL, ?, ?, ?, ?, ?)",
              (user_id, t_type, amount, desc, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Привет! Формат:\n💰 `/income 50000 Зарплата`\n💸 `/add 1500 Пятёрочка`\n📊 `/report`\n🤖 `/analyze`")

@bot.message_handler(commands=['income', 'add'])
def handle_transaction(message):
    try:
        parts = message.text.split(maxsplit=2)
        cmd = parts[0].replace('/', '')
        amount = float(parts[1])
        desc = parts[2] if len(parts) > 2 else ("Доход" if cmd == "income" else "Расход")
        t_type = "income" if cmd == "income" else "expense"
        add_transaction(message.chat.id, t_type, amount, desc)
        emoji = "✅ Доход" if t_type == "income" else "✅ Расход"
        bot.reply_to(message, f"{emoji} {amount} ₽ ({desc}) записан.")
    except Exception:
        bot.reply_to(message, "❌ Ошибка. Пример: `/add 1500 Продукты`")

@bot.message_handler(commands=['report'])
def report(message):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    month = datetime.now().strftime("%Y-%m")
    c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND type='income' AND date LIKE ?", (message.chat.id, f"{month}%"))
    inc = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND type='expense' AND date LIKE ?", (message.chat.id, f"{month}%"))
    exp = c.fetchone()[0]
    conn.close()
    bot.reply_to(message, f"📊 Отчёт за {datetime.now().strftime('%B %Y')}:\n💰 Доходы: {inc} ₽\n💸 Расходы: {exp} ₽\n📈 Баланс: {inc - exp} ₽")

@bot.message_handler(commands=['analyze'])
def analyze(message):
    if not client:
        bot.reply_to(message, "🤖 ИИ-анализ временно отключен (нет ключа OpenAI). Добавьте траты командой `/add`.")
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    month = datetime.now().strftime("%Y-%m")
    c.execute("SELECT description, amount FROM transactions WHERE user_id=? AND type='expense' AND date LIKE ?", (message.chat.id, f"{month}%"))
    expenses = c.fetchall()
    conn.close()
    if not expenses:
        bot.reply_to(message, "📭 Нет расходов за месяц.")
        return
    exp_text = "\n".join([f"- {d}: {a} ₽" for d, a in expenses])
    bot.reply_to(message, "🤖 Анализирую... Подождите ~10 сек.")
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Ты финансовый аналитик. Проанализируй расходы:\n{exp_text}\nВерни: 1. Категоризацию 2. 2 аномальные траты 3. 3 конкретных совета. Кратко, без выдумок."}],
            temperature=0.3)
        bot.reply_to(message, f"📋 Анализ:\n{resp.choices[0].message.content}")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка ИИ: {e}")

if __name__ == "__main__":
    print("🤖 Bot polling started...")
    bot.polling(none_stop=True)
