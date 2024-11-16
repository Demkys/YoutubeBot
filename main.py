import telebot
import os
import time
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Форматы качества, которые будут доступны пользователю
POPULAR_QUALITIES = ["144p", "360p", "480p", "720p", "1080p"]

# Функция создания инлайн кнопок
def create_quality_buttons():
    markup = InlineKeyboardMarkup()
    for quality in POPULAR_QUALITIES:
        markup.add(InlineKeyboardButton(quality, callback_data=quality))
    return markup

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 Привет! Отправь мне ссылку на YouTube видео.")

# Обработчик сообщений с ссылками на YouTube
@bot.message_handler(func=lambda message: "youtube.com" in message.text or "youtu.be" in message.text)
def handle_message(message):
    url = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "🔄 Загружаю информацию о видео...")

    try:
        ydl_opts = {"quiet": True, "skip_download": True, "cookiefile": "cookies.txt"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get('title', 'Видео')
            bot.send_message(chat_id, "Выберите качество видео:", reply_markup=create_quality_buttons())
            
            # Сохраняем данные видео
            bot.user_data = {"url": url, "title": title}

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при получении информации о видео: {e}")

# Обработчик инлайн кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    quality = call.data
    url = bot.user_data.get("url")
    title = bot.user_data.get("title")

    bot.send_message(chat_id, f"📥 Загружаю видео в {quality} качестве...")

    # Опции загрузки
    ydl_opts = {
        "format": f"bestvideo[height<={quality[:-1]}]+bestaudio/best[height<={quality[:-1]}]",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "cookiefile": "cookies.txt",
        "noplaylist": True
    }

    try:
        start_time = time.time()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info_dict)
            elapsed_time = time.time() - start_time
            download_speed = round(os.path.getsize(video_path) / 1024 / 1024 / elapsed_time, 2)

        bot.send_message(chat_id, f"✅ Видео загружено. Скорость загрузки: {download_speed} МБ/сек")
        bot.send_message(chat_id, "📤 Отправляю видео...")

        # Отправка видео пользователю
        with open(video_path, 'rb') as video_file:
            start_time = time.time()
            bot.send_video(chat_id, video_file)
            elapsed_time = time.time() - start_time
            video_size = os.path.getsize(video_path) / 1024 / 1024
            upload_speed = round(video_size / elapsed_time, 2)
        
        bot.send_message(chat_id, f"✅ Видео отправлено. Скорость отправки: {upload_speed} МБ/сек")

        # Удаляем видео после отправки
        os.remove(video_path)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при загрузке/отправке видео: {e}")

bot.polling(none_stop=True)
