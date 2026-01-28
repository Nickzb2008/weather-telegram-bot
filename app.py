# app.py - Виправлена версія без обробки сигналів
from flask import Flask, jsonify
import os
import logging
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

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

def run_bot_sync():
    """Синхронний запуск бота"""
    try:
        print("=" * 60)
        print("🇺🇦 UKRAINE WEATHER BOT")
        print("=" * 60)
        
        # Імпортуємо бібліотеки
        from telegram.ext import Application
        from bot import main
        
        # Запускаємо бота
        main()
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
        import traceback
        traceback.print_exc()

def start_bot():
    """Запуск бота в окремому потоці без asyncio event loop"""
    import threading
    bot_thread = threading.Thread(target=run_bot_sync, daemon=True)
    bot_thread.start()
    return bot_thread

if __name__ == '__main__':
    # Запускаємо бота
    logger.info("🔄 Starting Telegram bot...")
    bot_thread = start_bot()
    
    # Запускаємо Flask сервер
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    logger.info(f"🌐 Starting Flask server on {host}:{port}")
    
    # Запускаємо Flask без reloader
    app.run(host=host, port=port, debug=False, use_reloader=False)