import openai
import feedparser
import telebot
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
bot = telebot.TeleBot("8192884376:AAEqoKclZUWWPCYVBRUlOLj4SHSzWkCybp8")
CHANNEL_ID = "@kodvoli"

def generate_daily_post():
    prompt = (
        "Згенеруй коротку, містичну, патріотичну цитату або філософську думку "
        "у стилі українського каналу KodVoli, яка підійде як 'Рубрика дня'."
    )
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

def fetch_latest_news():
    feed = feedparser.parse("https://www.pravda.com.ua/rss/")
    top_article = feed.entries[0]
    return f"{top_article.title}\n{top_article.link}\n\n{top_article.summary}"

@bot.message_handler(commands=['daily'])
def send_daily_post(message):
    post = generate_daily_post()
    bot.send_message(CHANNEL_ID, f"**Рубрика дня ({datetime.now().strftime('%d.%m.%Y')}):**\n\n{post}", parse_mode="Markdown")

@bot.message_handler(commands=['news'])
def send_news_summary(message):
    news = fetch_latest_news()
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[
            {"role": "system", "content": "Ти містичний AI-аналітик для каналу KodVoli. Поясни новину стисло, глибоко й влучно."},
            {"role": "user", "content": news}
        ]
    )
    summary = response['choices'][0]['message']['content']
    bot.send_message(CHANNEL_ID, f"**Новина дня:**\n\n{summary}", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_comment(message):
    if message.chat.type == "supergroup":
        user_text = message.text
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {"role": "system", "content": "Ти дотепний, містичний AI-куратор каналу KodVoli, який відповідає з повагою, філософією та іронією."},
                {"role": "user", "content": user_text}
            ]
        )
        answer = response['choices'][0]['message']['content']
        bot.reply_to(message, answer)

bot.polling()
