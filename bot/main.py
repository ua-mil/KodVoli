import os
import feedparser
import telebot
import requests
import time
import schedule

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # для GPT
PICOGEN_API_KEY = os.getenv("PICOGEN_API_KEY")        # для Picogen

bot = telebot.TeleBot(BOT_TOKEN)
sent_links = set()

# === Генерація мем-коментаря через GPT (OpenRouter)
def generate_meme_text(title):
    try:
        prompt = (
            f"Напиши короткий іронічний мем-коментар українською мовою до новини: \"{title}\". "
            "Формат: 1-2 рядки, з сарказмом або патріотичним гумором."
        )
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
        print(f"[GPT ERROR] {e}")
        return "Без коментарів. Але ми все памʼятаємо."

# === Генерація картинки через Picogen
def generate_meme_image(prompt):
    try:
        picogen_prompt = f"Мем-ілюстрація до новини: {prompt}. У стилі сатиричного цифрового мистецтва."

        response = requests.post(
            "https://api.picogen.io/v1/generate",
            headers={
                "Authorization": f"Bearer {PICOGEN_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": picogen_prompt,
                "model": "stable-diffusion",
                "size": "1024x1024"
            }
        )

        data = response.json()
        return data["data"]["url"]
    except Exception as e:
        print(f"[Picogen ERROR] {e}")
        return None

# === Отримання новин і публікація
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
                summary = entry.summary
                link = entry.link

                meme = generate_meme_text(title)
                image_url = generate_meme_image(title)

                message = (
                    f"<b>{source}</b>\n"
                    f"<a href='{link}'>{title}</a>\n\n"
                    f"{summary}\n\n"
                    f"😏 <b>Мем:</b>\n{meme}"
                )

                try:
                    bot.send_message(CHAT_ID, message, parse_mode="HTML", disable_web_page_preview=False)
                    if image_url:
                        bot.send_photo(CHAT_ID, image_url, caption="🎨 Мем-ілюстрація", parse_mode="HTML")
                    print(f"Надіслано: {title}")
                except Exception as e:
                    print(f"[SEND ERROR] {e}")
                time.sleep(3)

# === Планування щогодини
schedule.every(1).hours.do(fetch_and_send_news)

if __name__ == "__main__":
    fetch_and_send_news()
    while True:
        schedule.run_pending()
        time.sleep(60)