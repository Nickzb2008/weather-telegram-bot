# app.py - Веб-сервер для Render
from flask import Flask, jsonify
import threading
import os
import logging

app = Flask(__name__)

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    """Головна сторінка"""
    return jsonify({
        'status': 'online',
        'service': 'Ukraine Weather Telegram Bot',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'status': '/status'
        }
    })

@app.route('/health')
def health_check():
    """Ендпоінт для перевірки здоров'я сервісу"""
    return jsonify({
        'status': 'healthy',
        'timestamp': get_current_timestamp()
    })

@app.route('/status')
def status():
    """Статус сервісу"""
    return jsonify({
        'service': 'Ukraine Weather Bot',
        'status': 'running',
        'port': int(os.getenv('PORT', 10000)),
        'environment': os.getenv('ENVIRONMENT', 'production'),
        'timestamp': get_current_timestamp()
    })

def get_current_timestamp():
    """Отримати поточну мітку часу"""
    from datetime import datetime
    return datetime.now().isoformat()

def run_bot():
    """Запустити бота в окремому потоці"""
    try:
        logger.info("Starting Telegram bot...")
        # Імпортуємо та запускаємо бота
        from bot import main
        main()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == '__main__':
    # Запускаємо бота в окремому потоці
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаємо веб-сервер
    port = int(os.getenv('PORT', 10000))
    logger.info(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)