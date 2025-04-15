import os
import feedparser
import telebot
import requests
import time
import schedule

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
sent_links = set()

# === AI запити ===
def generate_openrouter_response(prompt):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://yourproject.com",
                "X-Title": "KodVoliBot"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return ""

# === Основна логіка ===
def fetch_and_send_news():
    print("Оновлення новин...")
    feeds = {
        "УНІАН": "https://www.unian.ua/rss/index.rss",
        "Українська правда": "https://www.pravda.com.ua/rss/"
    }

    for source, url in feeds.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            if entry.link not in sent_links:
                sent_links.add(entry.link)

                title = entry.title
                link = entry.link

                quote = generate_openrouter_response(
                    f"Напиши філософську або містичну українську цитату, яка підійде до новини: \"{title}\""
                )

                meme = generate_openrouter_response(
                    f"Придумай короткий іронічний мем-коментар українською мовою до новини: \"{title}\". "
                    "Формат: короткий, як для Telegram-бота, максимум 1-2 рядки."
                )

                message = (
                    f"<b>{source}</b>\n"
                    f"<a href='{link}'>{title}</a>\n\n"
                    f"🧠 <i>{quote}</i>\n\n"
                    f"😏 <b>Мем:</b>\n{meme}"
                )

                try:
                    bot.send_message(CHAT_ID, message, parse_mode="HTML", disable_web_page_preview=False)
                    print(f"Надіслано новину: {title}")
                except Exception as e:
                    print(f"Помилка надсилання: {e}")
                time.sleep(3)

# === Планування ===
schedule.every(1).hours.do(fetch_and_send_news)

if __name__ == "__main__":
    fetch_and_send_news()
    while True:
        schedule.run_pending()
        time.sleep(60)