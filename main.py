import telebot
import os
import time
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 Привет! Отправь мне ссылку на YouTube видео.")

def create_quality_buttons(formats):
    markup = InlineKeyboardMarkup()
    for fmt in formats:
        res = fmt.get('format_note', 'unknown')
        ext = fmt.get('ext', 'mp4')
        btn_text = f"{res} - {ext}"
        markup.add(InlineKeyboardButton(btn_text, callback_data=f"{fmt['format_id']}"))
    return markup

@bot.message_handler(func=lambda message: "youtube.com" in message.text or "youtu.be" in message.text)
def handle_message(message):
    url = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "🔄 Загружаю информацию о видео...")

    try:
        ydl_opts = {"quiet": True, "skip_download": True, "cookiefile": "cookies.txt"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            title = info_dict.get('title', 'Видео')

        if not formats:
            bot.send_message(chat_id, "❌ Видео не найдено.")
            return

        bot.send_message(chat_id, "Выберите качество видео:", reply_markup=create_quality_buttons(formats))
        bot.user_data = {"url": url, "title": title, "formats": formats}

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при получении информации о видео: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    format_id = call.data

    url = bot.user_data.get("url")
    title = bot.user_data.get("title")
    bot.send_message(chat_id, f"🔄 Загружаю видео {title}...")

    try:
        ydl_opts = {
            "format": format_id,
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "quiet": True,
            "cookiefile": "cookies.txt",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info_dict)

        with open(video_path, 'rb') as video_file:
            bot.send_video(chat_id, video_file)

        os.remove(video_path)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при загрузке/отправке видео: {e}")

bot.polling(none_stop=True)
