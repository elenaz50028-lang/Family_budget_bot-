@bot.message_handler(commands=['analyze'])
def analyze(message):
    hf_token = os.getenv("HF_API_KEY")
    if not hf_token:
        bot.reply_to(message, "🤖 ИИ-ключ не настроен.")
        return

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    month = datetime.now().strftime("%Y-%m")
    c.execute("SELECT description, amount FROM transactions WHERE user_id=? AND type='expense' AND date LIKE ?", 
              (message.chat.id, f"{month}%"))
    expenses = c.fetchall()
    conn.close()

    if not expenses:
        bot.reply_to(message, "📭 Нет расходов за месяц.")
        return

    exp_text = "\n".join([f"- {d}: {a} ₽" for d, a in expenses])
    bot.reply_to(message, "🤖 Анализирую... Подождите ~20 сек.")

    try:
        from huggingface_hub import InferenceClient
        
        client = InferenceClient(token=hf_token)
        
        prompt = f"""Ты — семейный финансовый аналитик. Проанализируй расходы:
{exp_text}

Верни кратко:
1.  Категоризация
2. 🔍 1-2 аномалии
3. 💡 3 совета по экономии

Формат: список."""

        # Используем бесплатную модель
        response = client.chat_completion(
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        bot.reply_to(message, f"📋 Анализ:\n{response.choices[0].message.content}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка ИИ: {str(e)}")
