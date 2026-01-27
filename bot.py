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

print("=" * 50)
print("🚀 WEATHER BOT STARTING")
print("=" * 50)

# Перевірка змінних середовища
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found!")
    sys.exit(1)

print(f"✅ TELEGRAM_TOKEN: OK")
print(f"✅ WEATHER_API_KEY: {'OK' if WEATHER_API_KEY else 'NOT SET'}")
print("=" * 50)

# Імпорт бібліотек
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    import requests
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Run: pip install python-telegram-bot==20.7 requests==2.31.0")
    sys.exit(1)

class WeatherBot:
    def __init__(self):
        self.token = TELEGRAM_TOKEN
        self.weather_api_key = WEATHER_API_KEY
        self.application = None
        self.setup()
    
    def setup(self):
        """Налаштування бота"""
        try:
            # Створення Application за старим стилем (для версії 20.x)
            from telegram.ext import Updater
            
            # Для python-telegram-bot 20.x
            self.application = Application.builder().token(self.token).build()
            
            # Додавання обробників
            self.application.add_handler(CommandHandler("start", self.start))
            self.application.add_handler(CommandHandler("help", self.help))
            self.application.add_handler(CommandHandler("weather", self.weather))
            
            # Обробка текстових повідомлень
            self.application.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                self.handle_message
            ))
            
            # Обробник помилок
            self.application.add_error_handler(self.error_handler)
            
            logger.info("✅ Bot setup completed")
            print("✅ Bot setup completed")
            
        except Exception as e:
            logger.error(f"Setup error: {e}")
            print(f"❌ Setup error: {e}")
            raise
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка /start"""
        user = update.effective_user
        await update.message.reply_text(
            f"👋 Вітаю, {user.first_name}!\n\n"
            f"Я бот погоди. Надішліть мені назву міста.\n"
            f"Наприклад: Київ, Львів, Одеса\n\n"
            f"📋 Команди:\n"
            f"/start - початок\n"
            f"/help - довідка\n"
            f"/weather [місто] - погода"
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка /help"""
        await update.message.reply_text(
            "ℹ️ *Довідка:*\n\n"
            "*Команди:*\n"
            "/start - Початок роботи\n"
            "/help - Ця довідка\n"
            "/weather [місто] - Погода\n\n"
            "*Використання:*\n"
            "1. Надішліть назву міста\n"
            "2. Використайте /weather Київ\n"
            "3. Напишіть \"погода в Одесі\"",
            parse_mode='Markdown'
        )
    
    async def weather(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка /weather"""
        if not context.args:
            await update.message.reply_text("ℹ️ Напишіть: /weather [місто]\nНаприклад: /weather Київ")
            return
        
        city = ' '.join(context.args)
        await self.send_weather(update, city)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка текстових повідомлень"""
        text = update.message.text.strip().lower()
        logger.info(f"Message: {text}")
        
        # Список міст
        cities = ['київ', 'львів', 'одеса', 'харків', 'дніпро', 'полтава', 'запоріжжя']
        
        for city in cities:
            if city in text:
                await self.send_weather(update, city)
                return
        
        # Якщо не знайдено місто
        await update.message.reply_text(
            "🤔 Не розпізнано місто. Спробуйте:\n"
            "• Написати назву міста\n"
            "• Використати /weather Київ\n"
            "• Написати \"погода в Одесі\""
        )
    
    async def send_weather(self, update: Update, city: str):
        """Надіслати погоду"""
        try:
            msg = await update.message.reply_text(f"🔍 Шукаю погоду в {city.capitalize()}...")
            
            if not self.weather_api_key:
                await msg.edit_text(f"🌤 {city.capitalize()}\n\n(Weather API не налаштовано)")
                return
            
            # Отримання погоди
            weather_data = await self.get_weather_data(city)
            if weather_data:
                await msg.edit_text(weather_data, parse_mode='Markdown')
            else:
                await msg.edit_text(f"❌ Не вдалося отримати погоду для {city}")
                
        except Exception as e:
            logger.error(f"Weather error: {e}")
            await update.message.reply_text("❌ Помилка отримання погоди")
    
    async def get_weather_data(self, city):
        """Отримати дані погоди"""
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': city,
                'appid': self.weather_api_key,
                'units': 'metric',
                'lang': 'ua'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                city_name = data['name']
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                humidity = data['main']['humidity']
                description = data['weather'][0]['description']
                wind_speed = data['wind']['speed']
                
                return (
                    f"🌤 *Погода в {city_name}*\n\n"
                    f"📊 *Загальна інформація:*\n"
                    f"• Стан: {description.capitalize()}\n"
                    f"• Температура: {temp:.1f}°C\n"
                    f"• Відчувається як: {feels_like:.1f}°C\n\n"
                    f"💨 *Вітер:*\n"
                    f"• Швидкість: {wind_speed} м/с\n\n"
                    f"📈 *Інші параметри:*\n"
                    f"• Вологість: {humidity}%\n\n"
                    f"🔄 Дані з OpenWeatherMap"
                )
            return None
            
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return None
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробник помилок"""
        logger.error(f"Error: {context.error}")
    
    def run(self):
        """Запуск бота"""
        logger.info("🚀 Starting bot polling...")
        print("🚀 Starting bot polling...")
        
        try:
            self.application.run_polling(
                drop_pending_updates=True,
                timeout=30,
                pool_timeout=30
            )
        except Exception as e:
            logger.error(f"Polling error: {e}")
            print(f"❌ Polling error: {e}")
            raise

def main():
    """Головна функція"""
    try:
        bot = WeatherBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()