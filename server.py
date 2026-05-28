import os
from flask import Flask
import threading
from bot import bot

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Budget Bot is running on Render"

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    # Запускаем бота в фоновом потоке, чтобы Flask не блокировал polling
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
