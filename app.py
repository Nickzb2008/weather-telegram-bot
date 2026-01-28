# app.py - Веб-сервер для Render
from flask import Flask, jsonify
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

if __name__ == '__main__':
    # Запускаємо веб-сервер
    port = int(os.getenv('PORT', 10000))
    logger.info(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)