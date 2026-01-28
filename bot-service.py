# bot-service.py - Тільки Telegram бот
import os
import logging
import sys

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)

print("=" * 60)
print("🇺🇦 UKRAINE WEATHER BOT")
print("=" * 60)

if __name__ == '__main__':
    # Імпортуємо та запускаємо бота
    from bot import main
    main()