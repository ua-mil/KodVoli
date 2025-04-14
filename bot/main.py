import os
import feedparser
import telebot
import schedule
import time
import threading
from datetime import datetime
from openai import OpenAI

# === Ініціалізація OpenRouter ===
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID не встановлено")

# === Генерація цитати дня ===
def generate_daily_post():
    try:
        prompt = (
            "Згенеруй коротку, містичну, патріотичну цитату або філософську думку "
            "у стилі українського каналу KodVoli, яка підійде як 'Рубрика дня'."
        )
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[QUOTE] Помилка OpenRouter: {e}")
        return "Помилка генерації цитати. Спробуй пізніше."

# === Отримання новини ===
def fetch_latest_news():
    feed = feedparser.parse("https://www.pravda.com.ua/rss/")
    top_article = feed.entries[0]
    return f"{top_article.title}\n{top_article.link}\n\n{top_article.summary}"

# === Ручна команда /daily ===
@bot.message_handler(commands=['daily'])
def send_daily_post(message):
    post = generate_daily_post()
    bot.send_message(CHANNEL_ID, f"**Рубрика дня ({datetime.now().strftime('%d.%m.%Y')}):**\n\n{post}", parse_mode="Markdown")

# === Ручна команда /news ===
@bot.message_handler(commands=['news'])
def send_news_summary(message):
    try:
        news = fetch_latest_news()
        if len(news) > 2000:
            news = news[:1900] + "\n[...скоротили для GPT]"

        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ти містичний AI-аналітик каналу KodVoli. Поясни новину стисло, глибоко й влучно."},
                {"role": "user", "content": news}
            ]
        )
        summary = response.choices[0].message.content
        bot.send_message(CHANNEL_ID, f"**Новина дня:**\n\n{summary}", parse_mode="Markdown")

    except Exception as e:
        print(f"[NEWS] ПОМИЛКА: {e}")
        bot.send_message(CHANNEL_ID, "Помилка під час аналізу новини.")

# === Відповідь на коментарі ===
@bot.message_handler(func=lambda m: True)
def handle_comment(message):
    if message.chat.type == "supergroup":
        try:
            response = client.chat.completions.create(
                model="openai/gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ти AI-куратор каналу KodVoli. Відповідай філософсько, містично, з повагою і гумором."},
                    {"role": "user", "content": message.text}
                ]
            )
            answer = response.choices[0].message.content
            bot.reply_to(message, answer)
        except Exception as e:
            print(f"[COMMENT] ПОМИЛКА: {e}")

# === Автоматичне надсилання новини щогодини ===
def auto_hourly_news():
    try:
        news = fetch_latest_news()
        if len(news) > 2000:
            news = news[:1900] + "\n[...скоротили для GPT]"

        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ти AI-аналітик каналу KodVoli. Поясни новину містично і стисло."},
                {"role": "user", "content": news}
            ]
        )
        summary = response.choices[0].message.content
        bot.send_message(CHANNEL_ID, f"**Авто-новина ({datetime.now().strftime('%H:%M')}):**\n\n{summary}", parse_mode="Markdown")

    except Exception as e:
        print(f"[AUTO-NEWS] ПОМИЛКА: {e}")

# === Розклад: щогодини ===
schedule.every().hour.at(":00").do(auto_hourly_news)

# === Планувальник у фоні ===
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(30)

threading.Thread(target=run_scheduler, daemon=True).start()

# === Старт ===
print("KodVoli AI Bot (OpenRouter) запущено.")
bot.remove_webhook()
bot.polling()