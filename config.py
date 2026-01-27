import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    # Weather API
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    # Cache settings
    CACHE_DURATION = 600  # 10 хвилин у секундах
    
    # Bot settings
    DEFAULT_CITIES = {
        'полтава': 'Poltava',
        'київ': 'Kyiv',
        'львів': 'Lviv',
        'одеса': 'Odessa',
        'харків': 'Kharkiv',
        'дніпро': 'Dnipro',
        'запоріжжя': 'Zaporizhzhia'
    }

# Перевірка наявності ключів
if not Config.TELEGRAM_TOKEN:
    print("❌ Помилка: TELEGRAM_TOKEN не знайдено у .env файлі")
    exit(1)

if not Config.WEATHER_API_KEY:
    print("⚠️  Попередження: WEATHER_API_KEY не знайдено, погода не працюватиме")