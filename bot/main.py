import os
import time
import schedule
from dotenv import load_dotenv
import telebot
from openai import OpenAI

# Завантажуємо змінні оточення
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(BOT_TOKEN)

# Ініціалізація OpenRouter API клієнта
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# Функція для генерації контенту через OpenRouter
def generate_openrouter_response(prompt):
    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            extra_headers={
                "HTTP-Referer": "https://example.com",
                "X-Title": "KodVoli Bot"
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Помилка генерації: {e}"

# Основна функція для відправки щогодинного контенту
def send_hourly_content():
    news = generate_openrouter_response("Сгенеруй коротку актуальну новину на тему штучного інтелекту українською мовою.")
    quote = generate_openrouter_response("Надрукуй мотивуючу цитату українською мовою.")
    comment = generate_openrouter_response("Напиши короткий іронічний коментар до новини про ШІ українською мовою.")

    full_message = (
        f"📰 <b>НОВИНА ГОДИНИ</b>\n{news}\n\n"
        f"💬 <b>КОМЕНТАР</b>\n{comment}\n\n"
        f"📜 <b>ЦИТАТА</b>\n{quote}"
    )

    try:
        bot.send_message(CHAT_ID, full_message, parse_mode="HTML")
        print("Повідомлення надіслано.")
    except Exception as e:
        print(f"Помилка надсилання: {e}")

# Плануємо відправку щогодини
schedule.every().hour.at(":00").do(send_hourly_content)

# Запускаємо постійний цикл
if __name__ == "__main__":
    print("KodVoli AI Bot запущено. Очікуємо на годинну відправку...")
    send_hourly_content()  # Надіслати одразу при старті
    while True:
        schedule.run_pending()
        time.sleep(10)