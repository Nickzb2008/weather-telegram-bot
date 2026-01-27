import os
import logging
import sys

# ============================================================================
# НАЛАШТУВАННЯ ЛОГУВАННЯ - ВИДАЛИТИ filename='logs/bot.log'
# ========================================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout  # Тільки консоль на Render
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("🚀 WEATHER TELEGRAM BOT STARTING")
print("=" * 60)

# ============================================================================
# ПЕРЕВІРКА ЗМІННИХ СЕРЕДОВИЩА
# ============================================================================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

print(f"📋 Перевірка конфігурації:")
print(f"   TELEGRAM_TOKEN: {'✅ Налаштовано' if TELEGRAM_TOKEN else '❌ ВІДСУТНІЙ'}")
print(f"   WEATHER_API_KEY: {'✅ Налаштовано' if WEATHER_API_KEY else '⚠️  ВІДСУТНІЙ'}")
print("=" * 60)

if not TELEGRAM_TOKEN:
    print("❌ ПОМИЛКА: TELEGRAM_TOKEN не знайдено!")
    print("   Додайте змінну середовища TELEGRAM_TOKEN на Render")
    sys.exit(1)

# ============================================================================
# ІМПОРТ БІБЛІОТЕК
# ============================================================================
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        filters,
        ContextTypes
    )
except ImportError as e:
    logger.error(f"Помилка імпорту telegram бібліотек: {e}")
    print("❌ Помилка: python-telegram-bot не встановлено")
    print("   Додайте до requirements.txt: python-telegram-bot==20.7")
    sys.exit(1)

# ============================================================================
# ПРОСТА КОНФІГУРАЦІЯ (без config.py)
# ============================================================================
class Config:
    TELEGRAM_TOKEN = TELEGRAM_TOKEN
    WEATHER_API_KEY = WEATHER_API_KEY
    DEFAULT_CITIES = {
        "Київ": "Kyiv",
        "Львів": "Lviv",
        "Одеса": "Odesa",
        "Харків": "Kharkiv",
        "Дніпро": "Dnipro",
        "Запоріжжя": "Zaporizhzhia",
        "Вінниця": "Vinnytsia",
        "Полтава": "Poltava",
        "Чернігів": "Chernihiv",
        "Черкаси": "Cherkasy",
        "Житомир": "Zhytomyr",
        "Суми": "Sumy",
        "Тернопіль": "Ternopil",
        "Івано-Франківськ": "Ivano-Frankivsk",
        "Луцьк": "Lutsk",
        "Ужгород": "Uzhhorod",
        "Миколаїв": "Mykolaiv",
        "Херсон": "Kherson",
        "Рівне": "Rivne",
        "Чернівці": "Chernivtsi"
    }

# ============================================================================
# ПРОСТИЙ WEATHER API КЛАС (без окремого файлу)
# ============================================================================
import requests
import json
from datetime import datetime

class SimpleWeatherAPI:
    def __init__(self):
        self.api_key = Config.WEATHER_API_KEY
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.cache = {}
        logger.info("Weather API ініціалізовано")
    
    def get_weather(self, city_name):
        """Отримати погоду для міста"""
        if not self.api_key:
            return None
        
        # Пошук англійської назви міста
        city_en = None
        for ua_city, en_city in Config.DEFAULT_CITIES.items():
            if ua_city.lower() == city_name.lower() or en_city.lower() == city_name.lower():
                city_en = en_city
                break
        
        if not city_en:
            city_en = city_name
        
        # Кешування
        cache_key = city_en.lower()
        if cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if (datetime.now() - cache_time).seconds < 300:  # 5 хвилин кеш
                return data
        
        try:
            # Запит до API
            params = {
                'q': city_en,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'ua'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.cache[cache_key] = (datetime.now(), data)
                return data
            else:
                logger.error(f"API помилка: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Помилка запиту погоди: {e}")
            return None
    
    def format_weather_message(self, weather_data):
        """Форматування повідомлення про погоду"""
        try:
            city = weather_data['name']
            temp = weather_data['main']['temp']
            feels_like = weather_data['main']['feels_like']
            humidity = weather_data['main']['humidity']
            pressure = weather_data['main']['pressure']
            wind_speed = weather_data['wind']['speed']
            wind_deg = weather_data['wind'].get('deg', 0)
            description = weather_data['weather'][0]['description'].capitalize()
            
            # Напрямок вітру
            directions = ["Північний", "Північно-східний", "Східний", "Південно-східний",
                         "Південний", "Південно-західний", "Західний", "Північно-західний"]
            wind_dir = directions[round(wind_deg / 45) % 8] if wind_deg else "Не визначено"
            
            message = f"""
🌤 *Погода в {city}*

📊 *Загальна інформація:*
• Стан: *{description}*
• Температура: *{temp:.1f}°C*
• Відчувається як: *{feels_like:.1f}°C*

💨 *Вітер:*
• Швидкість: *{wind_speed} м/с*
• Напрямок: *{wind_dir}*
• Пориви: *{weather_data['wind'].get('gust', wind_speed * 1.5):.1f} м/с*

📈 *Інші параметри:*
• Вологість: *{humidity}%*
• Тиск: *{pressure} hPa*
• Видимість: *{weather_data.get('visibility', 'Н/Д')} м*

🔄 Оновлено: {datetime.now().strftime('%H:%M:%S')}
"""
            return message
            
        except Exception as e:
            logger.error(f"Помилка форматування погоди: {e}")
            return "❌ Помилка обробки даних погоди"

# ============================================================================
# ОСНОВНИЙ КЛАС БОТА
# ============================================================================
class WeatherBot:
    def __init__(self):
        self.logger = logger
        self.weather_api = SimpleWeatherAPI()
        
        # Створення додатку
        self.application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        
        # Реєстрація обробників
        self._register_handlers()
        
        self.logger.info("✅ Бот ініціалізовано")
        print("✅ Бот готовий до запуску")
    
    def _register_handlers(self):
        """Реєстрація обробників"""
        # Команди
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("weather", self.weather_command))
        self.application.add_handler(CommandHandler("cities", self.cities_command))
        
        # Обробка кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Обробка текстів
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))
        
        # Обробник помилок
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка /start"""
        user = update.effective_user
        self.logger.info(f"Користувач {user.id} виконав /start")
        
        welcome_text = f"""
👋 Вітаю, {user.first_name}!

Я бот погоди. Надішліть мені назву міста або натисніть кнопку:

📌 *Доступні команди:*
/weather [місто] - прогноз погоди
/cities - список доступних міст
/help - довідка

💡 *Приклади:*
• "Київ"
• "Погода в Одесі"
• "/weather Львів"
        """
        
        # Кнопки
        keyboard = [
            [InlineKeyboardButton("🌤 Київ", callback_data="city_Київ"),
             InlineKeyboardButton("🏙 Львів", callback_data="city_Львів")],
            [InlineKeyboardButton("🌊 Одеса", callback_data="city_Одеса"),
             InlineKeyboardButton("⚙️ Харків", callback_data="city_Харків")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def weather_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка /weather"""
        if not context.args:
            await update.message.reply_text(
                "ℹ️ Використання: /weather [назва міста]\n"
                "Наприклад: /weather Київ"
            )
            return
        
        city = ' '.join(context.args)
        await self._send_weather(update, city, is_command=True)
    
    async def cities_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показати список міст"""
        cities = "\n".join([f"• {city}" for city in Config.DEFAULT_CITIES.keys()])
        await update.message.reply_text(
            f"🏙 *Доступні міста:*\n\n{cities}\n\n"
            f"📝 Ви можете писати українською або англійською.",
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка /help"""
        help_text = """
ℹ️ *Довідка по боту*

*Основні команди:*
/start - початок роботи
/weather [місто] - прогноз погоди
/cities - список доступних міст
/help - ця довідка

*Як користуватися:*
1. Натисніть кнопку з містом
2. Напишіть назву міста
3. Використайте команду /weather [місто]

*Приклади:*
• "Київ"
• "Погода в Одесі?"
• "/weather Львів"

*Доступна інформація:*
• Температура та відчуття
• Вологість, тиск, видимість
• Вітер (швидкість, пориви, напрям)
• Загальний стан погоди
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка текстів"""
        text = update.message.text.strip()
        self.logger.info(f"Повідомлення: {text}")
        
        # Спрощений пошук міста
        text_lower = text.lower()
        
        for city_ua, city_en in Config.DEFAULT_CITIES.items():
            if city_ua.lower() in text_lower or city_en.lower() in text_lower:
                await self._send_weather(update, city_ua)
                return
        
        # Якщо просто текст без міста
        await update.message.reply_text(
            "🤔 Не вдалося розпізнати місто.\n\n"
            "📝 *Спробуйте так:*\n"
            "• Написати назву міста (наприклад, 'Київ')\n"
            "• Використати /cities для списку міст\n"
            "• Натиснути кнопку з містом\n"
            "• Використати /weather [місто]",
            parse_mode='Markdown'
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка кнопок"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith('city_'):
            city = query.data[5:]  # Видалити 'city_'
            await self._send_weather_by_query(query, city)
    
    async def _send_weather(self, update: Update, city: str, is_command=False):
        """Надіслати погоду"""
        try:
            if is_command:
                msg = await update.message.reply_text(f"🔍 Шукаю погоду в {city}...")
            else:
                msg = await update.message.reply_text(f"🔍 Аналізую погоду в {city}...")
            
            weather_data = self.weather_api.get_weather(city)
            
            if weather_data:
                message = self.weather_api.format_weather_message(weather_data)
                await msg.edit_text(message, parse_mode='Markdown')
                self.logger.info(f"Погода для {city} надіслана")
            else:
                error_msg = (
                    f"❌ Не вдалося отримати погоду для '{city}'.\n\n"
                    f"*Можливі причини:*\n"
                    f"• Місто не знайдено\n"
                    f"• Проблеми з підключенням\n"
                    f"• Неправильне написання\n\n"
                    f"📋 *Спробуйте:*\n"
                    f"• Перевірити написання міста\n"
                    f"• Використати /cities\n"
                    f"• Спробувати інше місто"
                )
                await msg.edit_text(error_msg, parse_mode='Markdown')
                self.logger.warning(f"Не знайдено погоду для {city}")
                
        except Exception as e:
            self.logger.error(f"Помилка: {e}")
            error_msg = "❌ Виникла помилка. Спробуйте пізніше."
            
            if is_command:
                await update.message.reply_text(error_msg)
            else:
                await msg.edit_text(error_msg)
    
    async def _send_weather_by_query(self, query, city: str):
        """Надіслати погоду (для кнопок)"""
        try:
            await query.edit_message_text(f"🔍 Отримую погоду для {city}...")
            weather_data = self.weather_api.get_weather(city)
            
            if weather_data:
                message = self.weather_api.format_weather_message(weather_data)
                await query.edit_message_text(message, parse_mode='Markdown')
                self.logger.info(f"Погода для {city} (кнопка) надіслана")
            else:
                await query.edit_message_text(
                    f"❌ Не вдалося отримати погоду для '{city}'\n"
                    f"Спробуйте інше місто."
                )
                
        except Exception as e:
            self.logger.error(f"Помилка кнопки: {e}")
            await query.edit_message_text("❌ Виникла помилка.")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обробка помилок"""
        self.logger.error(f"Помилка: {context.error}", exc_info=True)
    
    def run(self):
        """Запуск бота"""
        self.logger.info("🚀 Запускаю бота...")
        
        # Запуск полінгу
        self.application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )

# ============================================================================
# ГОЛОВНА ФУНКЦІЯ
# ============================================================================
def main():
    """Головна функція запуску"""
    print("🌍 Середовище: Render.com" if os.getenv('RENDER') else "🌍 Середовище: Локальне")
    print("=" * 60)
    
    try:
        bot = WeatherBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Бот зупинено")
        logger.info("Бот зупинено користувачем")
    except Exception as e:
        logger.error(f"Критична помилка: {e}", exc_info=True)
        print(f"\n❌ Критична помилка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()