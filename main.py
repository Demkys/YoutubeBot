import telebot
import os
import time
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Популярные качества
popular_qualities = ['144p', '360p', '480p', '720p', '1080p']

# Хранилище данных для каждого пользователя
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 Привет! Отправь мне ссылку на YouTube видео.")

def create_quality_buttons(available_formats):
    markup = InlineKeyboardMarkup()
    for fmt in available_formats:
        res = fmt.get('format_note')
        markup.add(InlineKeyboardButton(f"{res} (MP4)", callback_data=fmt['format_id']))
    return markup

@bot.message_handler(func=lambda message: "youtube.com" in message.text or "youtu.be" in message.text)
def handle_message(message):
    url = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "🔄 Загружаю информацию о видео...")

    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "cookiefile": "cookies.txt"  # Убедитесь, что файл cookies.txt в той же папке, что и скрипт
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            title = info_dict.get('title', 'Видео')

        # Фильтруем доступные форматы (только MP4 и популярные качества)
        available_formats = []
        for fmt in formats:
            res = fmt.get('format_note')
            ext = fmt.get('ext', 'mp4')
            acodec = fmt.get('acodec', 'none')
            if res in popular_qualities and ext == 'mp4' and acodec != 'none':
                available_formats.append(fmt)

        if not available_formats:
            bot.send_message(chat_id, "❌ Доступные форматы не найдены.")
            return

        bot.send_message(chat_id, "Выберите качество видео:", reply_markup=create_quality_buttons(available_formats))
        user_data[chat_id] = {"url": url, "title": title, "formats": available_formats}

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при получении информации о видео: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    format_id = call.data

    url = user_data[chat_id].get("url")
    title = user_data[chat_id].get("title")

    bot.send_message(chat_id, f"📥 Загружаю видео...")

    try:
        start_time = time.time()

        ydl_opts = {
            "format": f"{format_id}+bestaudio/best",
            "merge_output_format": "mp4",  # Объединяем видео и аудио в MP4
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "quiet": True,
            "cookiefile": "cookies.txt",  # Используем куки для обхода проверки
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info_dict)

        download_time = time.time() - start_time
        download_speed = os.path.getsize(video_path) / (1024 * 1024) / download_time  # МБ/сек
        bot.send_message(chat_id, f"📥 Видео загружено (Скорость: {download_speed:.2f} МБ/сек)")

        bot.send_message(chat_id, "📤 Отправляю видео...")
        start_send_time = time.time()

        with open(video_path, 'rb') as video_file:
            bot.send_video(chat_id, video_file)

        send_time = time.time() - start_send_time
        send_speed = os.path.getsize(video_path) / (1024 * 1024) / send_time  # МБ/сек
        bot.send_message(chat_id, f"📤 Видео отправлено (Скорость: {send_speed:.2f} МБ/сек)")

        os.remove(video_path)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при загрузке/отправке видео: {e}")

bot.polling(none_stop=True)
