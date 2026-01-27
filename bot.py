import os
import logging
import sys
import asyncio

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("🚀 SIMPLE WEATHER BOT STARTING")
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
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    print("✅ Libraries imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Глобальні змінні
bot_instance = None

async def start_command(update: Update, context):
    """Обробка команди /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привіт, {user.first_name}!\n\n"
        f"Я простий бот погоди. Просто напиши мені назву міста.\n\n"
        f"📋 Доступні міста:\n"
        f"• Київ\n• Львів\n• Одеса\n• Харків\n• Дніпро\n• Полтава\n\n"
        f"💡 Приклад: \"Київ\" або \"погода в Одесі\""
    )

async def help_command(update: Update, context):
    """Обробка команди /help"""
    await update.message.reply_text(
        "ℹ️ Довідка:\n\n"
        "Просто напишіть назву міста українською мовою.\n\n"
        "Доступні команди:\n"
        "/start - початок\n"
        "/help - довідка\n"
        "/weather [місто] - погода\n\n"
        "Приклади:\n"
        "• Київ\n"
        "• Погода в Львові\n"
        "• /weather Одеса"
    )

async def weather_command(update: Update, context):
    """Обробка команди /weather"""
    if context.args:
        city = ' '.join(context.args)
        await get_and_send_weather(update, city)
    else:
        await update.message.reply_text("ℹ️ Використання: /weather [місто]\nНаприклад: /weather Київ")

async def handle_message(update: Update, context):
    """Обробка текстових повідомлень"""
    text = update.message.text.strip().lower()
    logger.info(f"Повідомлення: {text}")
    
    # Список міст
    cities = ['київ', 'львів', 'одеса', 'харків', 'дніпро', 'полтава', 'запоріжжя']
    
    # Перевірка, чи є місто у тексті
    for city in cities:
        if city in text:
            await get_and_send_weather(update, city)
            return
    
    # Якщо не знайдено місто
    await update.message.reply_text(
        "🤔 Не знайшов місто у вашому запиті.\n\n"
        "📝 Спробуйте так:\n"
        "• Написати просто 'Київ'\n"
        "• Використати /weather Львів\n"
        "• Написати 'погода в Одесі'"
    )

async def get_and_send_weather(update: Update, city: str):
    """Отримати та надіслати погоду"""
    try:
        # Відправляємо повідомлення про завантаження
        message = await update.message.reply_text(f"🔍 Шукаю погоду в {city.capitalize()}...")
        
        if not WEATHER_API_KEY:
            await message.edit_text(f"🌤 {city.capitalize()}\n\n(Weather API ключ не налаштовано)")
            return
        
        # Отримуємо погоду
        weather_text = await fetch_weather(city)
        
        if weather_text:
            await message.edit_text(weather_text, parse_mode='Markdown')
        else:
            await message.edit_text(f"❌ Не вдалося отримати погоду для {city.capitalize()}")
            
    except Exception as e:
        logger.error(f"Помилка отримання погоди: {e}")
        await update.message.reply_text("❌ Помилка при отриманні погоди")

async def fetch_weather(city: str):
    """Отримати погоду з OpenWeatherMap"""
    try:
        # Перетворюємо українські назви на англійські
        city_map = {
            'київ': 'Kyiv',
            'львів': 'Lviv', 
            'одеса': 'Odesa',
            'харків': 'Kharkiv',
            'дніпро': 'Dnipro',
            'полтава': 'Poltava',
            'запоріжжя': 'Zaporizhzhia'
        }
        
        city_en = city_map.get(city, city)
        
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
            
            name = data.get('name', city.capitalize())
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            pressure = data['main']['pressure']
            description = data['weather'][0]['description'].capitalize()
            wind_speed = data['wind']['speed']
            
            return (
                f"🌤 *Погода в {name}*\n\n"
                f"📊 *Загальна інформація:*\n"
                f"• Стан: {description}\n"
                f"• Температура: *{temp:.1f}°C*\n"
                f"• Відчувається як: *{feels_like:.1f}°C*\n\n"
                f"💨 *Вітер:*\n"
                f"• Швидкість: *{wind_speed} м/с*\n\n"
                f"📈 *Інші параметри:*\n"
                f"• Вологість: *{humidity}%*\n"
                f"• Тиск: *{pressure} hPa*\n\n"
                f"🔄 Дані з OpenWeatherMap"
            )
        else:
            logger.error(f"API помилка: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Помилка API: {e}")
        return None

async def error_handler(update: Update, context):
    """Обробник помилок"""
    logger.error(f"Помилка: {context.error}")

async def main():
    """Головна асинхронна функція"""
    global bot_instance
    
    print("🚀 Creating application...")
    
    try:
        # Створюємо Application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        bot_instance = application.bot
        
        # Додаємо обробників
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("weather", weather_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Додаємо обробник помилок
        application.add_error_handler(error_handler)
        
        print("✅ Application created successfully")
        print("🚀 Starting bot polling...")
        
        # Запускаємо полінг
        await application.run_polling(
            drop_pending_updates=True,
            timeout=30,
            pool_timeout=30,
            allowed_updates=["message", "callback_query"]
        )
        
    except Exception as e:
        print(f"❌ Error in main: {e}")
        raise

def run_bot():
    """Запуск бота"""
    try:
        # Запускаємо асинхронну main функцію
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_bot()