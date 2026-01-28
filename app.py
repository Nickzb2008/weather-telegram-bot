# app.py - Версія для Koyeb
import os
import sys
import logging

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)

print("=" * 60)
print("🇺🇦 UKRAINE WEATHER BOT - KOYEB VERSION")
print("=" * 60)



TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found!")
    sys.exit(1)

print(f"✅ TELEGRAM_TOKEN: OK")
if OPENWEATHERMAP_API_KEY:
    print(f"✅ OPENWEATHERMAP_API_KEY: OK")
else:
    print(f"⚠️ OPENWEATHERMAP_API_KEY: Not found - altitude wind will be estimated")



if __name__ == '__main__':
    # Запускаємо бота напряму
    from bot import main
    main()