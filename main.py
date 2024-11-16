import os
from pytube import YouTube
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv

load_dotenv()

# Получаем токен из .env
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# Функция для старта
async def start(update: Update, context):
    await update.message.reply_text("Привет! Отправь ссылку на YouTube-видео или Shorts.")

# Функция для обработки сообщений с ссылками
async def handle_message(update: Update, context):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        await update.message.reply_text("Анализирую ссылку, пожалуйста подождите...")
        yt = YouTube(url)
        
        # Создаем инлайн-кнопки с выбором качества
        keyboard = []
        for stream in yt.streams.filter(progressive=True, file_extension='mp4'):
            quality = f"{stream.resolution} ({round(stream.filesize / 1024 / 1024)} MB)"
            button = InlineKeyboardButton(quality, callback_data=stream.itag)
            keyboard.append([button])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Выберите качество для загрузки видео '{yt.title}'", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Пожалуйста, отправьте корректную ссылку на YouTube.")

# Функция для обработки инлайн-кнопок
async def button_click(update: Update, context):
    query = update.callback_query
    itag = int(query.data)
    await query.answer()
    
    url = query.message.reply_to_message.text
    yt = YouTube(url)
    stream = yt.streams.get_by_itag(itag)
    
    # Статус загрузки
    await query.edit_message_text(f"Загружаю видео 📥 ({stream.resolution})...")
    
    # Скачиваем видео
    video_file = stream.download()
    
    # Статус отправки
    await query.edit_message_text("Отправляю видео 📤...")
    
    # Отправка видео в чат
    with open(video_file, 'rb') as file:
        await context.bot.send_video(chat_id=query.message.chat_id, video=file)

    # Удаляем файл после отправки
    os.remove(video_file)

# Главная функция запуска
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))

    print("Бот запущен!")
    await app.run_polling()  # Запуск бота

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())  # Используем asyncio.run для запуска основной функции
