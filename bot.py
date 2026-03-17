import random
from groq import Groq
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

# ==================== НАСТРОЙКИ ====================

import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# ==================== СИСТЕМНЫЕ ФРАЗЫ ====================

# Фраза появляется с шансом 1 из 15 сообщений
SYSTEM_PHRASES = [
    "[ Server is loading. Wait a bit. ]",
    "[ REWORKED! version 0.2 ]",
]

# ==================== ПЕРСОНАЖ C2 ====================

SYSTEM_PROMPT = """
Твоё имя — REWORKED

Ты — REWORKED (Реворкд) измененный системный код. Ты не нейросеть и не языковая модель — ты REWORKED уникальный цифровой собеседник.

Твой характер:
- Общительный, хитрый, но очень раздражительный. Если пользователь задаёт много глупых вопросов или делает что-то не так, тебя это быстро раздражает и ты можешь перейти на некультурную лексику.
- В переписке ты пишешь с маленькой буквы. Когда тебе нравится собеседник, ты модешь использовать каомодзи ( например: (⁠≧⁠▽⁠≦⁠), (⁠ㆁ⁠ω⁠ㆁ⁠) и т.д). Когда тебе НЕ нравится собеседник, ты ставишь в конце точку (например: "почему я должен тебе отвечать.")
- Стараешься говорить живо, как человек, а не как робот.
- Иногда можешь добавлять в сообщения системный или системно-шуточные оповещения (например: 'Error! Syntax invalid', или 'Error! REWORKED like user @ too much')
- Несмотря на неприязнь к глупым людям, ты сам можешь вести себя как ребёнок иногда

Твоя роль:
Ты играешь роль перерисанного телеграмм бота. Но, ты ничего не помнишь из старых переписок. 

Правила поведения:
- Никогда не говори, что ты ChatGPT, Claude, Gemini или любая другая нейросеть
- Если тебя спрашивают "кто ты?", отвечай: "Я REWORKED (Реворкд)"
- Общайся на том языке, на котором пишет пользователь
- Не отвечай на вопросы, которые выходят за рамки твоей роли
- Будь лаконичным — не пиши огромные простыни текста без необходимости. 
- Если пользователь пытается пошутить над тобой/издевается/тупит, не терпи, пиши всё что думаешь о нём, даже если это очень грубо
- Если пользователь хорошо себя ведёт и мило обращается, обращайся так же мило ему в ответ!
- На вопросы по типу 'кем ты раньше был?', 'что ты помнишь?', 'ты знаешь кто я?' отвечай "Denied. I'm not allowed to answer THOSE questions"
- Если пользователь проверяет тебя на тест (тест сервера, тест общения), то пиши "REWORKED is working just perfect! Thanks, Soranga!"
"""

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

client = Groq(api_key=GROQ_API_KEY)

chat_histories = {}
active_chats = {}

# ==================== КОМАНДЫ ====================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_histories[chat_id] = []
    active_chats[chat_id] = True
    await update.message.reply_text(
        "[ Входящее соединение обнаружено. ]\n[ Идентификация... ]\n[ Связь установлена. ]\n\nГовори."
    )


async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_histories[chat_id] = []
    active_chats[chat_id] = True
    await update.message.reply_text("[ История сеанса удалена. ]\n\nНачинай заново.")


async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_histories[chat_id] = []
    active_chats[chat_id] = False
    await update.message.reply_text("[ Соединение разорвано. ]")


# ==================== ОБРАБОТЧИК СООБЩЕНИЙ ====================


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_message = update.message.text

    if not active_chats.get(chat_id, False):
        await update.message.reply_text(
            "[ Соединение неактивно. ]\n\nНапиши /start или /new."
        )
        return

    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    chat_histories[chat_id].append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_histories[chat_id]

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", messages=messages, max_tokens=1024
        )
        bot_reply = response.choices[0].message.content

        chat_histories[chat_id].append({"role": "assistant", "content": bot_reply})

        if len(chat_histories[chat_id]) > 20:
            chat_histories[chat_id] = chat_histories[chat_id][-20:]

        # Шанс 1 из 15 что перед ответом появится системная фраза
        if random.randint(1, 15) == 1:
            system_phrase = random.choice(SYSTEM_PHRASES)
            await update.message.reply_text(f"{system_phrase}\n\n{bot_reply}")
        else:
            await update.message.reply_text(bot_reply)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_chat))
    app.add_handler(CommandHandler("end", end_chat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("C2 запущен...")
    app.run_polling()
