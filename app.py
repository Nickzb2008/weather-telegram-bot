# app.py - Головний файл для Koyeb (Flask + Telegram Bot)
from flask import Flask, jsonify
import threading
import os
import logging
import sys

app = Flask(__name__)

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    """Головна сторінка"""
    return jsonify({
        'status': 'online',
        'service': 'Ukraine Weather Telegram Bot',
        'version': '1.0.0'
    })

@app.route('/health')
def health_check():
    """Ендпоінт для перевірки здоров'я сервісу"""
    return jsonify({'status': 'healthy'})

def get_current_timestamp():
    """Отримати поточну мітку часу"""
    from datetime import datetime
    return datetime.now().isoformat()

def run_telegram_bot():
    """Запуск Telegram бота"""
    try:
        logger.info("Starting Telegram bot on Koyeb...")
        
        # Перевірка токена
        TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
        if not TELEGRAM_TOKEN:
            logger.error("❌ TELEGRAM_TOKEN not found in environment variables!")
            return
        
        logger.info("✅ TELEGRAM_TOKEN loaded successfully")
        
        # Імпорт тут, щоб уникнути проблем з Flask
        print("=" * 60)
        print("🇺🇦 UKRAINE WEATHER BOT ON KOYEB")
        print("=" * 60)
        
        # Імпорт необхідних бібліотек
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
        import asyncio
        
        # Імпорт власних модулів
        from settlements_db import settlements_db
        from weather_api import weather_api
        
        # Створення додатку
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Тут потрібно додати всі обробники з вашого bot.py
        # Наприклад:
        from bot import start_command, help_command, handle_message, button_handler, handle_menu_button
        from bot import get_main_keyboard
        
        # Додавання обробників
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(🌤|📅|🔍|🏙|⭐️|📊|❓|↩️)'), handle_menu_button))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print(f"✅ Database loaded: {len(settlements_db.settlements)} settlements")
        print("✅ Open-Meteo API: Ready")
        print("🚀 Starting bot polling on Koyeb...")
        
        # Запуск бота
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=None
        )
        
    except Exception as e:
        logger.error(f"❌ Error in Telegram bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Запускаємо Telegram бота в окремому потоці
    logger.info("🔄 Starting Telegram bot thread...")
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Запускаємо Flask веб-сервер
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    logger.info(f"🌐 Starting Flask server on {host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False)