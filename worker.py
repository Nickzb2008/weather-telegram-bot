# worker.py - Worker для Telegram бота
import os
import logging
import sys

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("🇺🇦 UKRAINE WEATHER BOT WORKER")
print("=" * 60)

# Перевірка змінних середовища
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found!")
    sys.exit(1)

print(f"✅ TELEGRAM_TOKEN: OK")
print("✅ OPEN-METEO: FREE TIER (no API key needed)")
print("=" * 60)

if __name__ == '__main__':
    # Імпортуємо та запускаємо бота
    from bot import main
    main()