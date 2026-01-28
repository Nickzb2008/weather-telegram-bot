# main.py - Основна точка входу для Koyeb
import os
import sys
import logging

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("🇺🇦 UKRAINE WEATHER BOT - KOYEB DEPLOYMENT")
print("=" * 60)

# Перевірка змінних середовища
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found!")
    print("Please set TELEGRAM_TOKEN environment variable on Koyeb")
    sys.exit(1)

print(f"✅ TELEGRAM_TOKEN: OK")
print("✅ OPEN-METEO: FREE TIER (no API key needed)")
print("=" * 60)

if __name__ == '__main__':
    # Імпортуємо та запускаємо бота
    try:
        from bot import main
        main()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)