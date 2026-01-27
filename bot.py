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
print("🚀 WEATHER BOT v21 STARTING")
print("=" * 60)

# Перевірка змінних середовища
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found!")
    print("Add TELEGRAM_TOKEN environment variable on Render")
    sys.exit(1)

print(f"✅ TELEGRAM_TOKEN: OK")
print(f"✅ WEATHER_API_KEY: {'OK' if WEATHER_API_KEY else 'NOT SET'}")
print("=" * 60)

# Імпорт бібліотек
try:
    import requests
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    print("✅ Libraries imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# ============================================================================
# ФУНКЦІЇ ДЛЯ ПОГОДИ
# ============================================================================

def get_weather(city_name):
    """Отримати погоду для міста"""
    if not WEATHER_API_KEY:
        return None
    
    # Мапінг міст
    city_map = {
        'київ': 'Kyiv', 'львів': 'Lviv', 'одеса': 'Odesa',
        'харків': 'Kharkiv', 'дніпро': 'Dnipro', 'полтава': 'Poltava',
        'запоріжжя': 'Zaporizhzhia', 'вінниця': 'Vinnytsia',
        'чернігів': 'Chernihiv', 'черкаси': 'Cherkasy'
    }
    
    city_en = city_map.get(city_name.lower(), city_name)
    
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city_en,
            'appid': WEATHER_API_KEY,
            'units': 'metric',
            'lang': 'ua'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            name = data.get('name', city_name.capitalize())
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            pressure = data['main']['pressure']
            description = data['weather'][0]['description'].capitalize()
            wind_speed = data['wind']['speed']
            wind_deg = data['wind'].get('deg', 0)
            
            # Напрямок вітру
            directions = ["Північний", "Північно-східний", "Східний", "Південно-східний",
                         "Південний", "Південно-західний", "Західний", "Північно-західний"]
            wind_dir = directions[round(wind_deg / 45) % 8] if wind_deg else "Не визначено"
            
            return (
                f"🌤 *Погода в {name}*\n\n"
                f"📊 *Загальна інформація:*\n"
                f"• Стан: *{description}*\n"
                f"• Температура: *{temp:.1f}°C*\n"
                f"• Відчувається як: *{feels_like:.1f}°C*\n\n"
                f"💨 *Вітер:*\n"
                f"• Швидкість: *{wind_speed} м/с*\n"
                f"• Напрямок: *{wind_dir}*\n\n"
                f"📈 *Інші параметри:*\n"
                f"• Вологість: *{humidity}%*\n"
                f"• Тиск: *{pressure} hPa*\n\n"
                f"🔄 Дані з OpenWeatherMap"
            )
        else:
            logger.error(f"API error: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return None

# ============================================================================
# ОБРОБНИКИ КОМАНД
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /start"""
    user = update.effective_user
    logger.info(f"User {user.id} started bot")
    
    await update.message.reply_text(
        f"👋 Вітаю, {user.first_name}!\n\n"
        f"Я бот погоди. Напишіть мені назву міста.\n\n"
        f"📋 *Доступні команди:*\n"
        f"/start - початок\n"
        f"/help - довідка\n"
        f"/weather [місто] - погода\n\n"
        f"💡 *Приклади:*\n"
        f"• Київ\n"
        f"• погода в Одесі\n"
        f"• /weather Львів",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /help"""
    await update.message.reply_text(
        "ℹ️ *Довідка по боту*\n\n"
        "*Як користуватися:*\n"
        "1. Напишіть назву міста\n"
        "2. Використайте команду /weather\n"
        "3. Запитайте про погоду\n\n"
        "*Приклади запитів:*\n"
        "• Київ\n"
        "• Яка погода у Львові?\n"
        "• Погода Одеса\n"
        "• /weather Харків\n\n"
        "*Доступні міста:*\n"
        "Київ, Львів, Одеса, Харків, Дніпро, Полтава, Запоріжжя, Вінниця",
        parse_mode='Markdown'
    )

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /weather"""
    if not context.args:
        await update.message.reply_text(
            "ℹ️ *Використання:* /weather [назва міста]\n\n"
            "*Приклади:*\n"
            "/weather Київ\n"
            "/weather Львів\n"
            "/weather Одеса",
            parse_mode='Markdown'
        )
        return
    
    city = ' '.join(context.args)
    await process_weather_request(update, city, is_command=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка текстових повідомлень"""
    text = update.message.text.strip().lower()
    logger.info(f"Message received: {text}")
    
    # Список міст для пошуку
    cities = ['київ', 'львів', 'одеса', 'харків', 'дніпро', 
              'полтава', 'запоріжжя', 'вінниця']
    
    # Ключові слова для погоди
    weather_keywords = ['погода', 'weather', 'температура', 'вітер']
    
    # Пошук міста
    found_city = None
    for city in cities:
        if city in text:
            found_city = city
            break
    
    # Якщо є ключові слова про погоду, спробуємо знайти місто
    if not found_city:
        for keyword in weather_keywords:
            if keyword in text:
                # Спрощений пошук міста після ключового слова
                parts = text.split(keyword)
                if len(parts) > 1:
                    potential_city = parts[1].strip()
                    # Видаляємо зайві слова
                    for word in ['в', 'у', 'на', 'for', 'in', 'at']:
                        potential_city = potential_city.replace(word, '').strip()
                    
                    if potential_city:
                        found_city = potential_city
                        break
    
    if found_city:
        await process_weather_request(update, found_city)
    else:
        # Якщо короткий текст, спробуємо як назву міста
        if len(text) < 20 and not any(keyword in text for keyword in weather_keywords):
            await process_weather_request(update, text)
        else:
            await update.message.reply_text(
                "🤔 *Не розпізнано запит.*\n\n"
                "📝 *Спробуйте так:*\n"
                "• Напишіть назву міста\n"
                "• Використайте /weather [місто]\n"
                "• Запитайте 'погода в [місті]'\n\n"
                "❓ *Довідка:* /help",
                parse_mode='Markdown'
            )

async def process_weather_request(update: Update, city: str, is_command=False):
    """Обробка запиту про погоду"""
    try:
        # Відправляємо повідомлення про завантаження
        if is_command:
            message = await update.message.reply_text(f"🔍 *Шукаю погоду в {city}...*", parse_mode='Markdown')
        else:
            message = await update.message.reply_text(f"🔍 *Аналізую погоду в {city}...*", parse_mode='Markdown')
        
        # Отримуємо погоду
        weather_text = get_weather(city)
        
        if weather_text:
            await message.edit_text(weather_text, parse_mode='Markdown')
            logger.info(f"Weather sent for {city}")
        else:
            await message.edit_text(
                f"❌ *Не вдалося отримати погоду для '{city}'*\n\n"
                f"*Можливі причини:*\n"
                f"• Місто не знайдено\n"
                f"• Проблеми з підключенням\n"
                f"• Неправильне написання\n\n"
                f"📋 *Спробуйте:*\n"
                f"• Перевірити написання\n"
                f"• Використати українську назву\n"
                f"• Спробувати інше місто",
                parse_mode='Markdown'
            )
            logger.warning(f"Weather not found for {city}")
            
    except Exception as e:
        logger.error(f"Error processing weather request: {e}")
        await update.message.reply_text(
            "❌ *Виникла помилка.*\n\n"
            "Будь ласка, спробуйте пізніше або зверніться до адміністратора.",
            parse_mode='Markdown'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник помилок"""
    logger.error(f"Bot error: {context.error}", exc_info=True)

# ============================================================================
# ГОЛОВНА ФУНКЦІЯ
# ============================================================================

def main():
    """Запуск бота"""
    try:
        print("🚀 Creating application...")
        
        # Створення додатку з новим API
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Додавання обробників
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("weather", weather_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Обробник помилок
        application.add_error_handler(error_handler)
        
        print("✅ Application created")
        print("🚀 Starting bot polling...")
        
        # Запуск бота
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
    main()