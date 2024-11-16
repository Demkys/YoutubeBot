import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time
from pytube import YouTube
from dotenv import load_dotenv

# Загрузка токена из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Отправь мне ссылку на YouTube видео, и я помогу скачать его. Выбери качество перед загрузкой!"
    )

# Обработчик сообщений с ссылками на видео
@bot.message_handler(func=lambda message: "youtube.com" in message.text or "youtu.be" in message.text)
def handle_message(message):
    url = message.text.strip()
    chat_id = message.chat.id

    bot.send_message(chat_id, "🔄 Загружаю информацию о видео, подожди...")

    try:
        # Получаем объект YouTube
        yt = YouTube(url)
        
        # Создаем инлайн-клавиатуру для выбора качества
        markup = InlineKeyboardMarkup()
        
        for stream in yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution'):
            btn_text = f"{stream.resolution} ({round(stream.filesize / 1024 / 1024, 2)} MB)"
            markup.add(InlineKeyboardButton(btn_text, callback_data=f"{stream.itag}|{url}"))
        
        # Отправляем сообщение с вариантами качества
        bot.send_message(chat_id, "Выберите качество для загрузки:", reply_markup=markup)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при получении видео: {e}")

# Обработчик нажатий на инлайн-кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    itag, url = call.data.split('|')
    chat_id = call.message.chat.id

    try:
        yt = YouTube(url)
        stream = yt.streams.get_by_itag(itag)

        # Сообщение о начале загрузки
        bot.send_message(chat_id, "📥 Загружаю видео, подожди немного...")

        start_time = time.time()
        video_path = stream.download(output_path="downloads/")
        download_duration = time.time() - start_time
        download_speed = round(stream.filesize / 1024 / 1024 / download_duration, 2)  # MB/sec

        bot.send_message(chat_id, f"✅ Загрузка завершена. Скорость загрузки: {download_speed} MB/сек")
        bot.send_message(chat_id, "📤 Отправляю видео...")

        # Отправка видео с расчетом скорости отправки
        with open(video_path, 'rb') as video_file:
            send_start_time = time.time()
            bot.send_video(chat_id, video_file)
            send_duration = time.time() - send_start_time
            send_speed = round(stream.filesize / 1024 / 1024 / send_duration, 2)  # MB/sec

        # Уведомление об успешной отправке и скорость
        bot.send_message(chat_id, f"✅ Видео отправлено! Скорость отправки: {send_speed} MB/сек")

        # Удаление файла после отправки
        os.remove(video_path)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка при отправке видео: {e}")

# Запуск бота
bot.polling(none_stop=True)
