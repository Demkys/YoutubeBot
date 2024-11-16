import os
import telebot
from pytube import YouTube
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
        yt = YouTube(url)
        
        # Создаем инлайн-кнопки с выбором качества
        markup = types.InlineKeyboardMarkup()
        for stream in yt.streams.filter(progressive=True, file_extension='mp4'):
            quality = f"{stream.resolution} ({round(stream.filesize / 1024 / 1024)} MB)"
            button = types.InlineKeyboardButton(text=quality, callback_data=str(stream.itag))
            markup.add(button)

        bot.send_message(message.chat.id, f"Выберите качество для загрузки видео '{yt.title}'", reply_markup=markup)
    else:
        bot.reply_to(message, "Пожалуйста, отправьте корректную ссылку на YouTube.")

# Обработка нажатия на инлайн кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    itag = int(call.data)
    url = call.message.reply_to_message.text
    yt = YouTube(url)
    stream = yt.streams.get_by_itag(itag)

    # Статус загрузки
    bot.edit_message_text(f"Загружаю видео 📥 ({stream.resolution})...", chat_id=call.message.chat.id, message_id=call.message.message_id)
    
    # Скачиваем видео
    video_file = stream.download()
    
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
