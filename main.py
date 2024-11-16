import telebot
import os
import time
import yt_dlp
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Загрузка токена из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Сообщение при старте
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 Привет! Отправь мне ссылку на YouTube видео, и я предложу тебе выбрать качество.")

# Создание инлайн-кнопок для выбора качества
def create_quality_buttons(formats):
    markup = InlineKeyboardMarkup()
    for fmt in formats:
        res = fmt.get('format_note', 'unknown')
        ext = fmt.get('ext', 'mp4')
        btn_text = f"{res} - {ext}"
        markup.add(InlineKeyboardButton(btn_text, callback_data=f"{fmt['format_id']}"))
    return markup

# Обработчик сообщений с ссылками на видео
@bot.message_handler(func=lambda message: "youtube.com" in message.text or "youtu.be" in message.text)
def handle_message(message):
    url = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "🔄 Загружаю информацию о видео...")

    try:
        # Получаем информацию о видео через yt-dlp
        ydl_opts = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])
            title = info_dict.get('title', 'Видео')
        
        if not formats:
            bot.send_message(chat_id, "❌ Видео не найдено. Попробуйте другую ссылку.")
            return

        # Выбор качества
        bot.send_message(chat_id, "Выберите качество видео:", reply_markup=create_quality_buttons(formats))
        
        # Сохранение данных в словаре
        bot.user_data = {"url": url, "title": title, "formats": formats}

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при получении информации о видео: {e}")

# Обработчик нажатий инлайн-кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    format_id = call.data

    url = bot.user_data.get("url")
    title = bot.user_data.get("title")

    bot.send_message(chat_id, f"🔄 Загружаю видео {title}...")

    try:
        # Загрузка видео через yt-dlp
        ydl_opts = {
            "format": format_id,
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "quiet": True
        }

        start_time = time.time()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info_dict)
        end_time = time.time()

        download_speed = round(info_dict['filesize'] / (end_time - start_time) / (1024 * 1024), 2)
        bot.send_message(chat_id, f"📥 Видео загружено (скорость загрузки: {download_speed} МБ/с)")

        # Отслеживание скорости отправки
        bot.send_message(chat_id, f"📤 Отправляю видео...")
        send_start_time = time.time()

        with open(video_path, 'rb') as video_file:
            bot.send_video(chat_id, video_file)

        send_end_time = time.time()
        send_speed = round(info_dict['filesize'] / (send_end_time - send_start_time) / (1024 * 1024), 2)
        bot.send_message(chat_id, f"✅ Видео отправлено (скорость отправки: {send_speed} МБ/с)")

        # Удаляем видео после отправки
        os.remove(video_path)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при загрузке/отправке видео: {e}")

# Запуск бота
bot.polling(none_stop=True)
