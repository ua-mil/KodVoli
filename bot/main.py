import os
import time
import requests
import feedparser
import telebot
import schedule

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(BOT_TOKEN)
sent_links = set()

# === Отримання курсу з НБУ
def get_real_exchange_rates():
    try:
        response = requests.get("https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json")
        data = response.json()
        usd = next((item for item in data if item["cc"] == "USD"), None)
        eur = next((item for item in data if item["cc"] == "EUR"), None)
        if not usd or not eur:
            return "Курси недоступні зараз."
        return (
            f"📅 Дата: {usd['exchangedate']}\n"
            f"💵 Долар: {usd['rate']} грн\n"
            f"💶 Євро: {eur['rate']} грн\n"
        )
    except Exception as e:
        print(f"[NBU ERROR] {e}")
        return "Помилка отримання курсу валют."

# === Курс BTC з Binance
def get_btc_rate():
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
        usd_rate = float(response.json()["price"])
        return f"₿ Біткойн: ${usd_rate:,.0f}"
    except Exception as e:
        print(f"[BTC ERROR] {e}")
        return "₿ Біткойн: недоступний"

# === Обʼєднаний курс
def get_rates():
    nbu = get_real_exchange_rates()
    btc = get_btc_rate()
    return f"{nbu}\n{btc}"

# === Надсилання новини з курсом
def fetch_and_send_news():
    print("Оновлення новин...")
    feeds = {
        "УНІАН": "https://www.unian.ua/rss/index.rss",
        "Українська правда": "https://www.pravda.com.ua/rss/"
    }

    for source, url in feeds.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:1]:
            if entry.link not in sent_links:
                sent_links.add(entry.link)

                title = entry.title
                summary = entry.summary
                link = entry.link

                msg = (
                    f"<b>{source}</b>\n"
                    f"<a href='{link}'>{title}</a>\n\n"
                    f"{summary}"
                )

                try:
                    bot.send_message(CHAT_ID, msg, parse_mode="HTML", disable_web_page_preview=False)
                    rates = get_rates()
                    bot.send_message(CHAT_ID, f"💱 <b>Офіційні курси валют:</b>\n{rates}", parse_mode="HTML")
                    print(f"Надіслано: {title}")
                except Exception as e:
                    print(f"[SEND ERROR] {e}")
                return

# === Команда /news
@bot.message_handler(commands=['news'])
def manual_news(message):
    if str(message.chat.id) != str(CHAT_ID).replace("@", ""):
        return
    fetch_and_send_news()

# === Команда /add
@bot.message_handler(commands=['add'])
def add_custom_news(message):
    if str(message.chat.id) != str(CHAT_ID).replace("@", ""):
        return
    msg = message.text.replace("/add", "").strip()
    if not msg:
        bot.reply_to(message, "Напиши текст новини після команди /add")
    else:
        bot.send_message(CHAT_ID, f"📰 <b>Авторська новина:</b>\n\n{msg}", parse_mode="HTML")
        rates = get_rates()
        bot.send_message(CHAT_ID, f"💱 <b>Офіційні курси валют:</b>\n{rates}", parse_mode="HTML")

# === Планування щогодини
schedule.every(1).hours.do(fetch_and_send_news)

# === Запуск
if __name__ == "__main__":
    fetch_and_send_news()
    while True:
        schedule.run_pending()
        time.sleep(60)
        bot.polling(none_stop=True)