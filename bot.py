import os
import logging
import sys
import json
from datetime import datetime
import asyncio

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("🚀 WEATHER BOT v2.0 WITH OPEN-METEO")
print("=" * 60)

# Перевірка змінних середовища
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')  # OpenWeatherMap (опціонально)

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found!")
    print("Add TELEGRAM_TOKEN environment variable on Render")
    sys.exit(1)

print(f"✅ TELEGRAM_TOKEN: OK")
print(f"✅ WEATHER_API_KEY: {'OK' if WEATHER_API_KEY else 'NOT SET (using Open-Meteo only)'}")
print("✅ OPEN-METEO: FREE TIER (no API key needed)")
print("=" * 60)

# Імпорт бібліотек
try:
    import requests
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
    print("✅ Libraries imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# ============================================================================
# БАЗА НАСЕЛЕНИХ ПУНКТІВ УКРАЇНИ
# ============================================================================

UKRAINE_CITIES = {
    "Київ": {"lat": 50.4501, "lon": 30.5234, "population": 2967000},
    "Харків": {"lat": 49.9935, "lon": 36.2304, "population": 1441000},
    "Одеса": {"lat": 46.4825, "lon": 30.7233, "population": 1017000},
    "Дніпро": {"lat": 48.4647, "lon": 35.0462, "population": 966000},
    "Львів": {"lat": 49.8397, "lon": 24.0297, "population": 717000},
    "Запоріжжя": {"lat": 47.8229, "lon": 35.1903, "population": 722000},
    "Кривий Ріг": {"lat": 47.9105, "lon": 33.3918, "population": 612000},
    "Миколаїв": {"lat": 46.9750, "lon": 31.9946, "population": 480000},
    "Вінниця": {"lat": 49.2328, "lon": 28.4816, "population": 369000},
    "Херсон": {"lat": 46.6354, "lon": 32.6169, "population": 283000},
    "Полтава": {"lat": 49.5883, "lon": 34.5514, "population": 279000},
    "Чернігів": {"lat": 51.4982, "lon": 31.2893, "population": 286000},
    "Черкаси": {"lat": 49.4444, "lon": 32.0598, "population": 269000},
    "Суми": {"lat": 50.9077, "lon": 34.7981, "population": 259000},
    "Житомир": {"lat": 50.2547, "lon": 28.6587, "population": 261000},
    "Хмельницький": {"lat": 49.4220, "lon": 26.9841, "population": 274000},
    "Чернівці": {"lat": 48.2921, "lon": 25.9358, "population": 265000},
    "Рівне": {"lat": 50.6199, "lon": 26.2516, "population": 246000},
    "Кропивницький": {"lat": 48.5132, "lon": 32.2597, "population": 222000},
    "Івано-Франківськ": {"lat": 48.9226, "lon": 24.7111, "population": 238000},
    "Тернопіль": {"lat": 49.5535, "lon": 25.5948, "population": 225000},
    "Луцьк": {"lat": 50.7472, "lon": 25.3254, "population": 217000},
    "Ужгород": {"lat": 48.6208, "lon": 22.2879, "population": 115000},
    "Біла Церква": {"lat": 49.7956, "lon": 30.1167, "population": 208000},
    "Калуш": {"lat": 49.0428, "lon": 24.3608, "population": 65000},
    "Бровари": {"lat": 50.5114, "lon": 30.7903, "population": 109000},
    "Мукачево": {"lat": 48.4412, "lon": 22.7176, "population": 85000},
    "Умань": {"lat": 48.7500, "lon": 30.2167, "population": 82000},
    "Бердичів": {"lat": 49.8917, "lon": 28.6000, "population": 75000},
}

CITY_NAMES = list(UKRAINE_CITIES.keys())

def find_cities_by_prefix(prefix):
    """Знайти міста за першими символами"""
    prefix_lower = prefix.lower()
    results = []
    
    for city in CITY_NAMES:
        if city.lower().startswith(prefix_lower):
            results.append(city)
    
    results.sort(key=lambda x: UKRAINE_CITIES[x]["population"], reverse=True)
    return results[:10]

def get_city_coordinates(city_name):
    """Отримати координати міста"""
    city_lower = city_name.lower()
    
    for city, data in UKRAINE_CITIES.items():
        if city.lower() == city_lower:
            return data["lat"], data["lon"]
    
    for city, data in UKRAINE_CITIES.items():
        if city_lower in city.lower():
            return data["lat"], data["lon"]
    
    return None, None

# ============================================================================
# OPEN-METEO API ФУНКЦІЇ
# ============================================================================

def get_openmeteo_weather(lat, lon):
    """
    Отримати повну інформацію про погоду з Open-Meteo
    Включає вітер на різних висотах
    """
    try:
        # Open-Meteo API запит
        url = "https://api.open-meteo.com/v1/forecast"
        
        # Параметри запиту - отримуємо ВСІ необхідні дані
        params = {
            'latitude': lat,
            'longitude': lon,
            'current': [
                'temperature_2m',           # Температура на 2м
                'relative_humidity_2m',     # Вологість
                'apparent_temperature',     # Температура, що відчувається
                'precipitation',            # Опади
                'rain',                     # Дощ
                'snowfall',                 # Сніг
                'weather_code',             # Код погоди
                'cloud_cover',              # Хмарність
                'pressure_msl',             # Тиск
                'surface_pressure',         # Тиск на поверхні
                'wind_speed_10m',           # Вітер на 10м
                'wind_direction_10m',       # Напрям вітру на 10м
                'wind_gusts_10m',           # Пориви вітру
            ],
            'hourly': [
                'wind_speed_10m',          # Для прогнозу
                'wind_direction_10m',
                'wind_speed_80m',          # Вітер на 80м (~400-600м)
                'wind_direction_80m',
                'wind_speed_120m',         # Вітер на 120м (~800м)
                'wind_direction_120m',
                'wind_speed_180m',         # Вітер на 180м (~1000м)
                'wind_direction_180m',
            ],
            'daily': [
                'sunrise', 'sunset',       # Схід/захід сонця
            ],
            'timezone': 'auto',
            'forecast_days': 1
        }
        
        logger.info(f"Requesting Open-Meteo for coordinates: {lat}, {lon}")
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            logger.info("Open-Meteo API response received successfully")
            return data
        else:
            logger.error(f"Open-Meteo API error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Open-Meteo API timeout")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Open-Meteo request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_openmeteo_weather: {e}")
        return None

def get_wind_direction(degrees):
    """Конвертувати градуси у назву напрямку вітру"""
    if degrees is None:
        return "Не визначено"
    
    directions = [
        "Північний", "Північно-східний", "Східний", "Південно-східний",
        "Південний", "Південно-західний", "Західний", "Північно-західний"
    ]
    index = round(degrees / 45) % 8
    return f"{directions[index]} ({int(degrees)}°)"

def get_weather_description(weather_code):
    """Отримати опис погоди за кодом Open-Meteo"""
    weather_codes = {
        0: "Ясне небо",
        1: "Переважно ясно",
        2: "Мінлива хмарність",
        3: "Хмарно",
        45: "Туман",
        48: "Покритий інеєм туман",
        51: "Легка мряка",
        53: "Помірна мряка",
        55: "Густа мряка",
        56: "Легка мряка з інеєм",
        57: "Густа мряка з інеєм",
        61: "Невеликий дощ",
        63: "Помірний дощ",
        65: "Сильний дощ",
        66: "Легкий дощ з інеєм",
        67: "Сильний дощ з інеєм",
        71: "Невеликий снігопад",
        73: "Помірний снігопад",
        75: "Сильний снігопад",
        77: "Сніжинки",
        80: "Невеликі зливи",
        81: "Помірні зливи",
        82: "Сильні зливи",
        85: "Невеликі снігові зливи",
        86: "Сильні снігові зливи",
        95: "Гроза",
        96: "Гроза з невеликим градом",
        99: "Гроза з сильним градом"
    }
    
    return weather_codes.get(weather_code, "Невідомо")

def calculate_cloud_base(temperature, humidity):
    """
    Розрахувати нижню кромку хмар (в метрах)
    Використовує формулу: висота = 125 * (температура - точка роси)
    """
    if temperature is None or humidity is None:
        return None
    
    # Формула для точки роси
    # t - температура, rh - відносна вологість
    t = temperature
    rh = humidity
    
    # Константи для формули Магнуса
    a = 17.27
    b = 237.7
    
    # Розрахунок точки роси
    alpha = ((a * t) / (b + t)) + math.log(rh / 100.0)
    dew_point = (b * alpha) / (a - alpha)
    
    # Розрахунок висоти хмар
    cloud_base = 125 * (t - dew_point)
    
    # Обмеження розумних значень
    if cloud_base < 100:
        return 100
    elif cloud_base > 5000:
        return 5000
    else:
        return int(cloud_base)

def format_weather_message(city_name, openmeteo_data):
    """Форматування повідомлення з даними Open-Meteo"""
    try:
        if not openmeteo_data or 'current' not in openmeteo_data:
            return None
        
        current = openmeteo_data['current']
        hourly = openmeteo_data.get('hourly', {})
        
        # Основні дані
        temp = current.get('temperature_2m', 0)
        feels_like = current.get('apparent_temperature', temp)
        humidity = current.get('relative_humidity_2m', 0)
        pressure = current.get('pressure_msl', 0)
        cloud_cover = current.get('cloud_cover', 0)
        weather_code = current.get('weather_code', 0)
        
        # Опади
        precipitation = current.get('precipitation', 0)
        rain = current.get('rain', 0)
        snowfall = current.get('snowfall', 0)
        
        # Вітер на землі (10м)
        wind_speed_10m = current.get('wind_speed_10m', 0)
        wind_dir_10m = current.get('wind_direction_10m')
        wind_gusts_10m = current.get('wind_gusts_10m', 0)
        
        # Отримуємо опис погоди
        weather_desc = get_weather_description(weather_code)
        
        # Розраховуємо нижню кромку хмар
        import math
        cloud_base = calculate_cloud_base(temp, humidity)
        
        # Вітер на висотах з поточного часу
        current_hour = datetime.now().hour
        wind_at_heights = {}
        
        if 'time' in hourly and 'wind_speed_80m' in hourly:
            times = hourly['time']
            current_index = 0
            
            # Знаходимо індекс поточного часу
            for i, time_str in enumerate(times):
                try:
                    hour = int(time_str.split('T')[1].split(':')[0])
                    if hour == current_hour:
                        current_index = i
                        break
                except:
                    continue
            
            # Вітер на різних висотах
            heights_data = [
                ('400m', 'wind_speed_80m', 'wind_direction_80m', 0.7),  # 80м * 0.7 ≈ 400м
                ('600m', 'wind_speed_80m', 'wind_direction_80m', 1.0),  # 80м ≈ 600м
                ('800m', 'wind_speed_120m', 'wind_direction_120m', 1.0),  # 120м ≈ 800м
                ('1000m', 'wind_speed_180m', 'wind_direction_180m', 1.0),  # 180м ≈ 1000м
            ]
            
            for height_name, speed_key, dir_key, factor in heights_data:
                if speed_key in hourly and dir_key in hourly:
                    speed_values = hourly[speed_key]
                    dir_values = hourly[dir_key]
                    
                    if len(speed_values) > current_index and len(dir_values) > current_index:
                        wind_at_heights[height_name] = {
                            'speed': speed_values[current_index] * factor,
                            'direction': dir_values[current_index],
                            'height': height_name
                        }
        
        # Формуємо повідомлення
        message = f"🌤 *Погода в {city_name}*\n\n"
        
        message += f"📊 *Загальна інформація:*\n"
        message += f"• Стан: *{weather_desc}*\n"
        message += f"• Температура: *{temp:.1f}°C*\n"
        message += f"• Відчувається як: *{feels_like:.1f}°C*\n"
        message += f"• Вологість: *{humidity}%*\n"
        message += f"• Тиск: *{pressure:.0f} hPa*\n\n"
        
        # Вітер на землі
        wind_dir_text = get_wind_direction(wind_dir_10m)
        message += f"💨 *Вітер на землі (10м):*\n"
        message += f"• Швидкість: *{wind_speed_10m:.1f} м/с*\n"
        message += f"• Пориви: *{wind_gusts_10m:.1f} м/с*\n"
        message += f"• Напрямок: *{wind_dir_text}*\n\n"
        
        # Вітер на висотах
        if wind_at_heights:
            message += f"🌀 *Вітер на висотах:*\n"
            for height in ['400m', '600m', '800m', '1000m']:
                if height in wind_at_heights:
                    data = wind_at_heights[height]
                    wind_dir = get_wind_direction(data['direction'])
                    message += f"• {height}: *{data['speed']:.1f} м/с*, {wind_dir}\n"
            message += f"\n"
        
        # Опади
        message += f"🌧 *Опади:*\n"
        message += f"• За останню годину: *{precipitation:.1f} мм*\n"
        message += f"• Дощ: *{rain:.1f} мм*\n"
        message += f"• Сніг: *{snowfall:.1f} мм*\n\n"
        
        # Хмарність
        message += f"☁️ *Хмарність:*\n"
        message += f"• Рівень: *{cloud_cover}%*\n"
        if cloud_base:
            message += f"• Нижня кромка хмар: *{cloud_base} м*\n"
        else:
            message += f"• Нижня кромка хмар: *Не визначено*\n"
        
        # Додаємо інформацію про джерело
        message += f"\n📡 *Джерело даних:* Open-Meteo API\n"
        message += f"🔄 Оновлено: {datetime.now().strftime('%H:%M')}"
        
        return message
        
    except Exception as e:
        logger.error(f"Error formatting Open-Meteo message: {e}")
        return None

# ============================================================================
# ОБРОБНИКИ КОМАНД (спрощені)
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /start"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🌤 Популярні міста", callback_data="popular_cities")],
        [InlineKeyboardButton("🔍 Пошук міста", callback_data="search_city")],
        [InlineKeyboardButton("❓ Допомога", callback_data="help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Вітаю, {user.first_name}!\n\n"
        f"Я бот погоди з використанням Open-Meteo API.\n"
        f"🔹 *Детальна інформація про вітер на висотах*\n"
        f"🔹 *Автодоповнення міст України*\n"
        f"🔹 *Повністю безкоштовно*\n\n"
        f"Почніть вводити назву міста (наприклад 'ки' для Києва):",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /help"""
    await update.message.reply_text(
        "ℹ️ *Довідка по боту*\n\n"
        "*Основні можливості:*\n"
        "• Детальна інформація про вітер на 5 висотах\n"
        "• Автодоповнення назв міст\n"
        "• Дані з Open-Meteo API (безкоштовно)\n\n"
        "*Як користуватися:*\n"
        "1. Почніть вводити назву міста (мінімум 2 символи)\n"
        "2. Оберіть місто зі списку\n"
        "3. Отримайте детальний прогноз\n\n"
        "*Приклади:*\n"
        "• 'ки' → Київ\n"
        "• 'ль' → Львів\n"
        "• 'пол' → Полтава\n\n"
        "*Команди:*\n"
        "/start - початок\n"
        "/help - довідка\n"
        "/find [частина] - пошук міст",
        parse_mode='Markdown'
    )

async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пошук міст за частиною назви"""
    if not context.args:
        await update.message.reply_text(
            "🔍 *Пошук міста*\n\n"
            "Використання: /find [частина назви]\n\n"
            "*Приклади:*\n"
            "/find ки\n"
            "/find ль\n"
            "/find пол",
            parse_mode='Markdown'
        )
        return
    
    prefix = ' '.join(context.args)
    results = find_cities_by_prefix(prefix)
    
    if results:
        cities_list = "\n".join([f"• {city}" for city in results])
        await update.message.reply_text(
            f"🔍 *Результати пошуку для '{prefix}':*\n\n"
            f"{cities_list}\n\n"
            f"ℹ️ Натисніть на назву міста для погоди.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Не знайдено міст, що починаються на '{prefix}'",
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка текстових повідомлень з автодоповненням"""
    text = update.message.text.strip()
    
    if text.startswith('/'):
        return
    
    if len(text) >= 2:
        results = find_cities_by_prefix(text)
        
        if results:
            if len(results) == 1:
                await process_weather_request(update, results[0])
                return
            
            elif len(results) <= 5:
                keyboard = []
                for city in results:
                    keyboard.append([InlineKeyboardButton(
                        f"🌤 {city}", 
                        callback_data=f"city_{city}"
                    )])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"🔍 Знайдено {len(results)} міста(ів):\nОберіть потрібне:",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                return
    
    await update.message.reply_text(
        "🤔 Не вдалося розпізнати місто.\n\n"
        "📝 *Поради:*\n"
        "• Почніть вводити назву (мінімум 2 символи)\n"
        "• Використайте /find для пошуку\n"
        "• Приклад: 'ки' → Київ",
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка натискання кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "popular_cities":
        popular_cities = sorted(
            UKRAINE_CITIES.items(), 
            key=lambda x: x[1]['population'], 
            reverse=True
        )[:8]
        
        keyboard = []
        for city, info in popular_cities:
            keyboard.append([InlineKeyboardButton(
                f"🌤 {city}", 
                callback_data=f"city_{city}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🏙 *Популярні міста України:*\nОберіть місто:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif data == "search_city":
        await query.edit_message_text(
            "🔍 *Пошук міста*\n\n"
            "Введіть назву міста або перші літери:\n\n"
            "*Приклади:*\n"
            "• Київ\n"
            "• ки\n"
            "• пол\n\n"
            "📝 Мінімум 2 символи для пошуку.",
            parse_mode='Markdown'
        )
    
    elif data == "help":
        await help_command(query, context)
    
    elif data.startswith("city_"):
        city = data[5:]
        await query.edit_message_text(
            f"🔍 Завантажую погоду для {city}...",
            parse_mode='Markdown'
        )
        await process_weather_request(query, city)

async def process_weather_request(update: Update, city: str):
    """Обробка запиту про погоду з Open-Meteo"""
    try:
        # Отримуємо координати
        lat, lon = get_city_coordinates(city)
        
        if not lat or not lon:
            error_msg = f"❌ Місто '{city}' не знайдено в базі."
            if hasattr(update, 'message'):
                await update.message.reply_text(error_msg, parse_mode='Markdown')
            else:
                await update.edit_message_text(error_msg, parse_mode='Markdown')
            return
        
        # Відправляємо повідомлення про завантаження
        if hasattr(update, 'message'):
            message = await update.message.reply_text(
                f"🔍 Отримую дані для {city}...", 
                parse_mode='Markdown'
            )
        else:
            message = await update.edit_message_text(
                f"🔍 Отримую дані для {city}...", 
                parse_mode='Markdown'
            )
        
        # Отримуємо дані з Open-Meteo
        weather_data = get_openmeteo_weather(lat, lon)
        
        if not weather_data:
            error_text = (
                f"❌ Не вдалося отримати погоду для {city}\n\n"
                f"Можливі причини:\n"
                f"• Проблеми з підключенням до Open-Meteo\n"
                f"• Тимчасовий збій сервісу\n"
                f"• Спробуйте через хвилину"
            )
            await message.edit_text(error_text, parse_mode='Markdown')
            return
        
        # Форматуємо повідомлення
        weather_text = format_weather_message(city, weather_data)
        
        if not weather_text:
            error_text = f"❌ Помилка обробки даних для {city}"
            await message.edit_text(error_text, parse_mode='Markdown')
            return
        
        await message.edit_text(weather_text, parse_mode='Markdown')
        logger.info(f"Weather sent for {city}")
            
    except Exception as e:
        logger.error(f"Error processing weather request: {e}")
        error_msg = "❌ Виникла критична помилка. Спробуйте пізніше."
        
        if hasattr(update, 'message'):
            await update.message.reply_text(error_msg, parse_mode='Markdown')
        else:
            await update.edit_message_text(error_msg, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник помилок"""
    logger.error(f"Bot error: {context.error}", exc_info=True)

# ============================================================================
# ГОЛОВНА ФУНКЦІЯ
# ============================================================================

def main():
    """Запуск бота"""
    try:
        print("🚀 Creating Telegram application...")
        
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Додавання обробників
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("find", find_command))
        
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        application.add_error_handler(error_handler)
        
        print("✅ Application created")
        print(f"✅ Cities database: {len(UKRAINE_CITIES)} cities")
        print("✅ Open-Meteo API: Ready (free tier)")
        print("🚀 Starting bot polling...")
        
        application.run_polling(
            drop_pending_updates=True,
            timeout=30,
            pool_timeout=30,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Application error: {e}")
        raise

if __name__ == '__main__':
    # Додаємо math для розрахунків
    import math
    main()