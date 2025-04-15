import os
import feedparser
import telebot
import requests
import time
import schedule
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
sent_links = set()

# === Генерація мем-коментаря
def generate_meme_text(title):
    try:
        prompt = (
            f"Напиши короткий іронічний мем-коментар українською мовою до новини: \"{title}\". "
            "Формат: 1-2 рядки, з сарказмом або бойовим патріотизмом."
        )
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://kodvoli.ua",
                "X-Title": "KodVoliBot"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[GPT ERROR] {e}")
        return "Без коментарів. Але ми памʼятаємо."

# === Генерація зображення через безкоштовний генератор
def generate_meme_image(prompt):
    try:
        response = requests.get(
            f"https://ai-image-generator.vercel.app/api?prompt={prompt}"
        )
        if response.status_code == 200:
            img_path = "meme.jpg"
            with open(img_path, "wb") as f:
                f.write(response.content)
            return img_path
        else:
            print(f"[IMAGE GENERATOR ERROR] {response.status_code}")
            return None
    except Exception as e:
        print(f"[IMAGE ERROR] {e}")
        return None

# === Додаємо рамку + підпис KodVoli
def add_frame_and_logo(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        border = 20
        width, height = img.size

        new_img = Image.new("RGB", (width + 2 * border, height + 2 * border), color=(0, 0, 0))
        new_img.paste(img, (border, border))

        draw = ImageDraw.Draw(new_img)
        font = ImageFont.load_default()
        text = "KodVoli"
        text_width, text_height = draw.textsize(text, font)
        x = (new_img.width - text_width) // 2
        y = new_img.height - text_height - 10
        draw.text((x, y), text, font=font, fill=(255, 255, 255))

        out_path = "meme_framed.jpg"
        new_img.save(out_path)
        return out_path
    except Exception as e:
        print(f"[FRAME ERROR] {e}")
        return image_path

# === Новини + мем
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

                meme_text = generate_meme_text(title)
                image_raw = generate_meme_image(title)
                image_final = add_frame_and_logo(image_raw) if image_raw else None

                msg = (
                    f"<b>{source}</b>\n"
                    f"<a href='{link}'>{title}</a>\n\n"
                    f"{summary}\n\n"
                    f"😏 <b>Мем:</b>\n{meme_text}"
                )

                try:
                    bot.send_message(CHAT_ID, msg, parse_mode="HTML", disable_web_page_preview=False)
                    if image_final:
                        bot.send_photo(CHAT_ID, open(image_final, "rb"), caption="🎨 Мем-ілюстрація")
                    print(f"Надіслано: {title}")
                except Exception as e:
                    print(f"[SEND ERROR] {e}")
                time.sleep(3)

# === Запуск щогодини
schedule.every(1).hours.do(fetch_and_send_news)

if __name__ == "__main__":
    fetch_and_send_news()
    while True:
        schedule.run_pending()
        time.sleep(60)