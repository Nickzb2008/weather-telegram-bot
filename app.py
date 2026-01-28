# app.py - Flask + Telegram Bot разом
from flask import Flask, jsonify
import os
import logging
import sys
import threading
import asyncio

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
        'service': 'weather-telegram-bot',
        'version': '1.0.0'
    })

@app.route('/health')
def health_check():
    """Health check для Koyeb"""
    return jsonify({'status': 'healthy'})

def start_bot_in_thread():
    """Запуск Telegram бота в окремому потоці"""
    try:
        print("=" * 60)
        print("🇺🇦 UKRAINE WEATHER BOT")
        print("=" * 60)
        
        # Імпортуємо бібліотеки тут, щоб уникнути конфліктів
        import asyncio
        
        # Створюємо новий event loop для цього потоку
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Імпортуємо основний код бота
        from bot import main
        
        # Запускаємо бота в цьому event loop
        loop.run_until_complete(main_async())
        
    except Exception as e:
        logger.error(f"Error in bot thread: {e}")
        import traceback
        traceback.print_exc()

async def main_async():
    """Асинхронна версія main з bot.py"""
    # Копіюємо код з bot.py main(), але з async
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    if not TELEGRAM_TOKEN:
        print("❌ ERROR: TELEGRAM_TOKEN not found!")
        return
    
    print(f"✅ TELEGRAM_TOKEN: OK")
    print("✅ OPEN-METEO: FREE TIER (no API key needed)")
    print("=" * 60)
    
    try:
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
        print("✅ Libraries imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return
    
    from settlements_db import settlements_db
    from weather_api import weather_api
    
    print(f"✅ Database loaded: {len(settlements_db.settlements)} settlements")
    print("✅ Open-Meteo API: Ready")
    print("🚀 Starting bot polling...")
    
    try:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Імпортуємо обробники з bot.py
        from bot import start_command, help_command, handle_message, button_handler, handle_menu_button
        
        # Додаємо обробники
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(🌤|📅|🔍|🏙|⭐️|📊|❓|↩️)'), handle_menu_button))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Додаємо обробник помилок
        from bot import error_handler
        application.add_error_handler(error_handler)
        
        # Запускаємо бота
        await application.run_polling(
            drop_pending_updates=True,
            timeout=30,
            pool_timeout=30,
            allowed_updates=None
        )
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        raise

if __name__ == '__main__':
    # Запускаємо бота в окремому потоці
    logger.info("🔄 Starting Telegram bot in separate thread...")
    bot_thread = threading.Thread(target=start_bot_in_thread, daemon=True)
    bot_thread.start()
    
    # Запускаємо Flask сервер
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    logger.info(f"🌐 Starting Flask server on {host}:{port}")
    
    # Важливо: use_reloader=False для уникнення подвійного запуску
    app.run(host=host, port=port, debug=False, use_reloader=False)