import os
import time
import schedule
import telebot
from openai import OpenAI
from datetime import datetime

# Зчитуємо змінні з Railway Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(BOT_TOKEN)

# OpenRouter через OpenAI SDK
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# Генерація відповіді
def generate_openrouter_response(prompt):
    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            extra_headers={
                "HTTP-Referer": "https://kodvoli.ua",  # можеш змінити або залишити
                "X-Title": "KodVoli AI Bot"
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[OPENROUTER ERROR] {e}")
        return "Помилка генерації."

# Надсилання щогодини
def send_hourly_update():
    print(f"[{datetime.now().strftime('%H:%M')}] Генеруємо автооновлення...")
    news = generate_openrouter_response("Сгенеруй коротку актуальну новину на тему штучного інтелекту українською мовою.")
    comment = generate_openrouter_response("Напиши короткий коментар або іронічну думку про ШІ українською мовою.")
    quote = generate_openrouter_response("Напиши коротку містичну або філософську цитату для українського каналу KodVoli.")

    full_message = (
        f"🕐 <b>Автооновлення {datetime.now().strftime('%H:%M')}:</b>\n\n"
        f"📰 <b>Новина:</b>\n{news}\n\n"
        f"💬 <b>Коментар:</b>\n{comment}\n\n"
        f"📜 <b>Цитата:</b>\n{quote}"
    )

    try:
        bot.send_message(CHAT_ID, full_message, parse_mode="HTML")
        print("Надіслано!")
    except Exception as e:
        print(f"[SEND ERROR] {e}")

# Планування щогодини
schedule.every().hour.at(":00").do(send_hourly_update)

# Старт циклу
if __name__ == "__main__":
    print("KodVoli AI Bot (OpenRouter) запущено.")
    send_hourly_update()  # одразу при старті
    while True:
        schedule.run_pending()
        time.sleep(10)