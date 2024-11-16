import os
import yt_dlp as youtube_dl
import telebot
from dotenv import load_dotenv
from telebot import types

# Загрузка токена из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Команда start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь ссылку на YouTube-видео или Shorts.")

# Обработка сообщений с ссылками
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if "youtube.com" in url or "youtu.be" in url:
        bot.reply_to(message, "Анализирую ссылку, пожалуйста подождите...")
        
        # Используем yt-dlp для получения информации о видео
        ydl_opts = {
            'format': 'bestaudio/bestvideo',
            'quiet': True,
            'extractaudio': False,  # Отключаем извлечение аудио
            'outtmpl': 'downloads/%(id)s.%(ext)s',  # Папка для загрузки
        }
        
        # Информация о видео
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get('title', None)
            formats = info_dict.get('formats', [])
            
            # Создаем инлайн-кнопки с выбором качества
            markup = types.InlineKeyboardMarkup()
            for fmt in formats:
                quality = f"{fmt['format_note']} ({fmt['ext'].upper()})"
                button = types.InlineKeyboardButton(text=quality, callback_data=fmt['format_id'])
                markup.add(button)

            bot.send_message(message.chat.id, f"Выберите качество для загрузки видео '{video_title}'", reply_markup=markup)
    else:
        bot.reply_to(message, "Пожалуйста, отправьте корректную ссылку на YouTube.")

# Обработка нажатия на инлайн кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    format_id = call.data
    url = call.message.reply_to_message.text
    
    # Используем yt-dlp для скачивания видео
    ydl_opts = {
        'format': format_id,
        'outtmpl': 'downloads/%(id)s.%(ext)s',  # Папка для загрузки
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_file = ydl.prepare_filename(info_dict)
    
    # Статус загрузки
    bot.edit_message_text(f"Загружаю видео 📥 ({info_dict['title']})...", chat_id=call.message.chat.id, message_id=call.message.message_id)
    
    # Статус отправки
    bot.edit_message_text("Отправляю видео 📤...", chat_id=call.message.chat.id, message_id=call.message.message_id)
    
    # Отправка видео в чат
    with open(video_file, 'rb') as file:
        bot.send_video(call.message.chat.id, video=file)

    # Удаляем файл после отправки
    os.remove(video_file)

# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
