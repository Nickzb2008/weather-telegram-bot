import os
import logging
import sys
import json
from datetime import datetime
import asyncio
from typing import Dict, List, Optional, Tuple
import math

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("🇺🇦 UKRAINE WEATHER BOT WITH COMPLETE SETTLEMENTS DATABASE")
print("=" * 60)

# Перевірка змінних середовища
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found!")
    print("Add TELEGRAM_TOKEN environment variable on Render")
    sys.exit(1)

print(f"✅ TELEGRAM_TOKEN: OK")
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

# Імпорт власних модулів
from settlements_db import settlements_db
from weather_api import WeatherAPI

# Ініціалізація API погоди
weather_api = WeatherAPI()

# ============================================================================
# ОБРОБНИКИ КОМАНД
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - головне меню"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🔍 Пошук населеного пункту", callback_data="search")],
        [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
        [InlineKeyboardButton("📊 Статистика бази", callback_data="database_stats")],
        [InlineKeyboardButton("📍 Моє місто", callback_data="my_city")],
        [InlineKeyboardButton("⭐️ Улюблені міста", callback_data="favorites")],
        [InlineKeyboardButton("⚙️ Налаштування", callback_data="settings")],
        [InlineKeyboardButton("❓ Допомога", callback_data="help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Вітаю, {user.first_name}!\n\n"
        f"🇺🇦 *Український бот погоди*\n\n"
        f"📋 *Особливості:*\n"
        f"• База {len(settlements_db.settlements)} населених пунктів\n"
        f"• Підтримка міст з однаковою назвою в різних областях\n"
        f"• Детальна інформація про вітер на 5 висотах\n"
        f"• Автодоповнення назв\n"
        f"• Збереження улюблених міст\n\n"
        f"✍️ *Почніть вводити назву населеного пункту або виберіть опцію:*",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = (
        "ℹ️ *Довідка по боту*\n\n"
        "*Пошук населених пунктів:*\n"
        "1. Почніть вводити назву (мінімум 2 символи)\n"
        "2. Якщо є кілька пунктів з однаковою назвою - оберіть область\n"
        "3. Отримайте детальний прогноз погоди\n\n"
        "*Приклади запитів:*\n"
        "• 'ки' → Київ\n"
        "• 'нов' → покаже всі пункти, що починаються на 'нов'\n"
        "• 'первомайськ' → покаже обидва Первомайськи\n\n"
        "*Основні команди:*\n"
        "/start - головне меню\n"
        "/help - ця довідка\n"
        "/find [назва] - пошук населеного пункту\n"
        "/regions - список областей\n"
        "/stats - статистика бази даних\n"
        "/favorites - улюблені міста\n"
        "/settings - налаштування\n\n"
        "*Інформація про погоду:*\n"
        "• Температура повітря\n"
        "• Вітер на землі та висотах 400, 600, 800, 1000 м\n"
        "• Напрям вітру в градусах\n"
        "• Вологість повітря\n"
        "• Опади (дощ, сніг)\n"
        "• Нижня кромка хмар\n"
        "• Тиск\n"
        "• Видимість"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /find - пошук населеного пункту"""
    if not context.args:
        await update.message.reply_text(
            "🔍 *Пошук населеного пункту*\n\n"
            "Використання: /find [назва або частина назви]\n\n"
            "*Приклади:*\n"
            "/find ки\n"
            "/find нов\n"
            "/find первомайськ\n\n"
            "📝 *Порада:* Мінімум 2 символи",
            parse_mode='Markdown'
        )
        return
    
    search_query = ' '.join(context.args)
    await search_settlements(update, search_query, context)

async def regions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /regions - список областей України"""
    regions = settlements_db.get_all_regions()
    regions_text = "\n".join([f"• {region}" for region in regions])
    
    keyboard = [
        [InlineKeyboardButton(f"🌤 {region}", callback_data=f"region_{region}")]
        for region in regions[:8]  # Показуємо перші 8 областей
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📋 *Області України:*\n\n{regions_text}\n\n"
        f"ℹ️ Всього: {len(regions)} областей\n\n"
        f"Оберіть область для перегляду міст:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - статистика бази даних"""
    stats = settlements_db.get_statistics()
    
    stats_text = f"📊 *Статистика бази даних:*\n\n"
    stats_text += f"• Унікальних назв: *{stats['unique_names']}*\n"
    stats_text += f"• Загальна кількість записів: *{stats['total_entries']}*\n"
    stats_text += f"• Областей: *{stats['regions_count']}*\n\n"
    
    stats_text += "*Топ-5 найбільших міст:*\n"
    for i, city in enumerate(stats['largest_cities'][:5], 1):
        stats_text += f"{i}. {city['name']} ({city['region']}): {city['population']:,} чол.\n"
    
    if stats['duplicates_count'] > 0:
        stats_text += f"\nℹ️ *Дублікати назв:* {stats['duplicates_count']}\n"
        for dup in stats['duplicates'][:3]:
            stats_text += f"• {dup}\n"
        if stats['duplicates_count'] > 3:
            stats_text += f"• ... та ще {stats['duplicates_count'] - 3} інших\n"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /favorites - улюблені міста"""
    user_id = update.effective_user.id
    favorites = context.user_data.get('favorites', [])
    
    if not favorites:
        keyboard = [
            [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
            [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⭐️ *Улюблені міста*\n\n"
            "У вас ще немає улюблених міст.\n\n"
            "Додайте місто до улюблених, щоб швидко отримувати погоду.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    keyboard = []
    for i, fav in enumerate(favorites):
        keyboard.append([
            InlineKeyboardButton(f"🌤 {fav['name']} ({fav['region']})", 
                               callback_data=f"weather_{fav['name']}_{fav['region']}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🗑 Очистити улюблені", callback_data="clear_favorites"),
        InlineKeyboardButton("🔍 Додати ще", callback_data="search")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    favorites_text = "\n".join([f"• {fav['name']} ({fav['region']})" for fav in favorites])
    
    await update.message.reply_text(
        f"⭐️ *Ваші улюблені міста:*\n\n{favorites_text}\n\n"
        f"Оберіть місто для перегляду погоди:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /settings - налаштування"""
    user_id = update.effective_user.id
    
    keyboard = [
        [InlineKeyboardButton("🔔 Сповіщення", callback_data="notifications")],
        [InlineKeyboardButton("🎨 Тема", callback_data="theme")],
        [InlineKeyboardButton("🌡 Одиниці виміру", callback_data="units")],
        [InlineKeyboardButton("↩️ Назад", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚙️ *Налаштування бота*\n\n"
        "Тут ви можете налаштувати:\n"
        "• Сповіщення про погоду\n"
        "• Тему інтерфейсу\n"
        "• Одиниці виміру температури\n\n"
        "Оберіть опцію для налаштування:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка текстових повідомлень"""
    text = update.message.text.strip()
    
    if text.startswith('/'):
        return
    
    # Перевіряємо, чи це номер з попереднього пошуку
    if 'last_search_results' in context.user_data and text.isdigit():
        index = int(text) - 1
        results = context.user_data['last_search_results']
        
        if 0 <= index < len(results):
            settlement = results[index]
            await process_weather_request(update, settlement['name'], settlement['region'])
            # Очищуємо результати пошуку
            context.user_data.pop('last_search_results', None)
            return
    
    # Перевіряємо, чи містить назву області в дужках
    import re
    pattern = r'(.+?)\s*\(([^)]+)\)'
    match = re.match(pattern, text)
    
    if match:
        settlement_name = match.group(1).strip()
        region = match.group(2).strip()
        
        # Шукаємо точне співпадіння
        results = settlements_db.find_settlements_by_name(settlement_name, region)
        if results:
            await process_weather_request(update, settlement_name, region)
            return
    
    # Звичайний пошук
    if len(text) >= 2:
        await search_settlements(update, text, context)
    else:
        keyboard = [
            [InlineKeyboardButton("🔍 Пошук населеного пункту", callback_data="search")],
            [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
            [InlineKeyboardButton("❓ Допомога", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤔 *Не розпізнано запит.*\n\n"
            "📝 *Формати запитів:*\n"
            "• Назва населеного пункту (напр. 'Київ')\n"
            "• Частина назви (напр. 'ки')\n"
            "• Назва з областю (напр. 'Новоград (Житомирська)')\n"
            "• Номер з попереднього списку\n\n"
            "ℹ️ Мінімум 2 символи для пошуку",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

# ============================================================================
# ПОШУК ТА ОБРОБКА НАСЕЛЕНИХ ПУНКТІВ
# ============================================================================

async def search_settlements(update: Update, query: str, context: Optional[ContextTypes.DEFAULT_TYPE] = None):
    """Пошук населених пунктів"""
    if len(query) < 2:
        await update.message.reply_text(
            "❌ *Занадто короткий запит.*\n\n"
            "Введіть мінімум 2 символи для пошуку.",
            parse_mode='Markdown'
        )
        return
    
    settlements = settlements_db.find_settlements_by_prefix(query, limit=20)
    
    if not settlements:
        keyboard = [
            [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
            [InlineKeyboardButton("❓ Допомога", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"❌ *Не знайдено населених пунктів за запитом '{query}'*\n\n"
            f"📝 *Поради:*\n"
            f"• Перевірте написання\n"
            f"• Спробуйте іншу частину назви\n" 
            f"• Використовуйте українську мову",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    # Якщо знайдено тільки один результат - одразу показуємо погоду
    if len(settlements) == 1:
        settlement = settlements[0]
        await process_weather_request(update, settlement['name'], settlement['region'])
        return
    
    # Якщо кілька результатів - показуємо список
    message = f"🔍 *Знайдено {len(settlements)} населених пунктів:*\n\n"
    
    # Групуємо за назвою (якщо є дублікати)
    grouped_results = {}
    for settlement in settlements:
        if settlement['name'] not in grouped_results:
            grouped_results[settlement['name']] = []
        grouped_results[settlement['name']].append(settlement)
    
    # Формуємо список
    for i, (name, items) in enumerate(grouped_results.items(), 1):
        if len(items) == 1:
            # Один пункт з такою назвою
            settlement = items[0]
            pop_str = f" ({settlement['population']:,} чол.)" if settlement['population'] > 0 else ""
            message += f"{i}. {name} ({settlement['region']}){pop_str}\n"
        else:
            # Кілька пунктів з однаковою назвою
            message += f"{i}. {name}:\n"
            for j, settlement in enumerate(items, 1):
                pop_str = f" ({settlement['population']:,} чол.)" if settlement['population'] > 0 else ""
                message += f"   {j}. {settlement['region']}{pop_str}\n"
    
    message += "\n📝 *Виберіть номер пункту або напишіть повну назву з вказанням області*"
    
    # Зберігаємо результати пошуку в контексті
    if context and hasattr(update, 'message'):
        context.user_data['last_search_results'] = settlements
        context.user_data['last_search_query'] = query
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def process_weather_request(update: Update, settlement_name: str, region: str):
    """Обробка запиту про погоду"""
    try:
        # Повідомлення про завантаження
        if hasattr(update, 'message'):
            message = await update.message.reply_text(
                f"🔍 Отримую погоду для {settlement_name} ({region})...", 
                parse_mode='Markdown'
            )
        else:
            message = await update.edit_message_text(
                f"🔍 Отримую погоду для {settlement_name} ({region})...", 
                parse_mode='Markdown'
            )
        
        # Отримуємо координати
        lat, lon = settlements_db.get_coordinates(settlement_name, region)
        
        if not lat or not lon:
            error_msg = f"❌ Не знайдено координат для '{settlement_name}' ({region})"
            if hasattr(update, 'message'):
                await update.message.reply_text(error_msg, parse_mode='Markdown')
            else:
                await update.edit_message_text(error_msg, parse_mode='Markdown')
            return
        
        # Отримуємо погоду
        weather_data = weather_api.get_weather(lat, lon)
        
        if not weather_data:
            error_text = (
                f"❌ Не вдалося отримати погоду для {settlement_name} ({region})\n\n"
                f"Можливі причини:\n"
                f"• Проблеми з підключенням\n"
                f"• Тимчасовий збій сервісу\n"
                f"• Спробуйте через хвилину"
            )
            await message.edit_text(error_text, parse_mode='Markdown')
            return
        
        # Форматуємо повідомлення
        weather_text = weather_api.format_weather_message(settlement_name, region, weather_data)
        
        if not weather_text:
            error_text = f"❌ Помилка обробки даних для {settlement_name}"
            await message.edit_text(error_text, parse_mode='Markdown')
            return
        
        # Додаємо кнопки дій
        keyboard = [
            [
                InlineKeyboardButton("⭐️ Додати до улюблених", callback_data=f"add_fav_{settlement_name}_{region}"),
                InlineKeyboardButton("🔄 Оновити", callback_data=f"weather_{settlement_name}_{region}")
            ],
            [
                InlineKeyboardButton("🏙 Інші міста області", callback_data=f"region_cities_{region}"),
                InlineKeyboardButton("🔍 Новий пошук", callback_data="search")
            ],
            [
                InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.edit_text(weather_text, parse_mode='Markdown', reply_markup=reply_markup)
        logger.info(f"Weather sent for {settlement_name} ({region})")
            
    except Exception as e:
        logger.error(f"Error processing weather request: {e}")
        error_msg = "❌ Виникла критична помилка. Спробуйте пізніше."
        
        if hasattr(update, 'message'):
            await update.message.reply_text(error_msg, parse_mode='Markdown')
        else:
            await update.edit_message_text(error_msg, parse_mode='Markdown')

# ============================================================================
# ОБРОБНИКИ КНОПОК
# ============================================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка натискання кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "main_menu":
        await start_command(query, context)
    
    elif data == "search":
        await query.edit_message_text(
            "🔍 *Пошук населеного пункту*\n\n"
            "Введіть назву або частину назви:\n\n"
            "*Приклади:*\n"
            "• Київ\n"
            "• ки\n"
            "• нов\n"
            "• Первомайськ (Миколаївська)\n\n"
            "📝 Мінімум 2 символи",
            parse_mode='Markdown'
        )
    
    elif data == "regional_centers":
        await show_regional_centers(query)
    
    elif data == "database_stats":
        await show_database_stats(query)
    
    elif data == "my_city":
        await handle_my_city(query, context)
    
    elif data == "favorites":
        await favorites_command(query, context)
    
    elif data == "settings":
        await settings_command(query, context)
    
    elif data == "help":
        await show_help(query)
    
    elif data.startswith("weather_"):
        parts = data.split('_')
        if len(parts) >= 3:
            settlement_name = parts[1]
            region = '_'.join(parts[2:])
            await query.edit_message_text(
                f"🔍 Завантажую погоду для {settlement_name} ({region})...",
                parse_mode='Markdown'
            )
            await process_weather_request(query, settlement_name, region)
    
    elif data.startswith("region_"):
        region = data.replace("region_", "")
        await show_region_cities(query, region)
    
    elif data.startswith("region_cities_"):
        region = data.replace("region_cities_", "")
        await show_region_cities(query, region, show_back_button=True)
    
    elif data.startswith("add_fav_"):
        parts = data.split('_')
        if len(parts) >= 4:
            settlement_name = parts[2]
            region = '_'.join(parts[3:])
            await add_to_favorites(query, context, settlement_name, region)
    
    elif data == "clear_favorites":
        await clear_favorites(query, context)
    
    elif data in ["notifications", "theme", "units"]:
        await show_settings_option(query, data)

async def show_regional_centers(query):
    """Показати обласні центри"""
    regional_centers = settlements_db.get_regional_centers()
    
    # Формуємо список
    centers_list = ""
    for i, center in enumerate(regional_centers[:10], 1):
        centers_list += f"{i}. {center['name']} ({center['region']}): {center['population']:,} чол.\n"
    
    # Створюємо кнопки
    keyboard = []
    for center in regional_centers[:8]:
        keyboard.append([InlineKeyboardButton(
            f"🌤 {center['name']}", 
            callback_data=f"weather_{center['name']}_{center['region']}"
        )])
    
    keyboard.append([
        InlineKeyboardButton("🔍 Пошук", callback_data="search"),
        InlineKeyboardButton("↩️ Назад", callback_data="main_menu")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🏙 *Обласні центри України:*\n\n{centers_list}\n"
        f"Оберіть місто для отримання погоди:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_database_stats(query):
    """Показати статистику бази даних"""
    stats = settlements_db.get_statistics()
    
    stats_text = f"📊 *Статистика бази даних:*\n\n"
    stats_text += f"• Унікальних назв: *{stats['unique_names']}*\n"
    stats_text += f"• Загальна кількість записів: *{stats['total_entries']}*\n"
    stats_text += f"• Областей: *{stats['regions_count']}*\n\n"
    
    stats_text += "*Топ-5 найбільших міст:*\n"
    for i, city in enumerate(stats['largest_cities'][:5], 1):
        stats_text += f"{i}. {city['name']} ({city['region']}): {city['population']:,} чол.\n"
    
    keyboard = [
        [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
        [InlineKeyboardButton("↩️ Назад", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_text, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_my_city(query, context):
    """Обробка кнопки 'Моє місто'"""
    user_id = query.from_user.id
    my_city = context.user_data.get('my_city')
    
    if my_city:
        await query.edit_message_text(
            f"📍 *Ваше місто:* {my_city['name']} ({my_city['region']})\n\n"
            f"Завантажую погоду...",
            parse_mode='Markdown'
        )
        await process_weather_request(query, my_city['name'], my_city['region'])
    else:
        keyboard = [
            [InlineKeyboardButton("🔍 Вибрати місто", callback_data="search")],
            [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
            [InlineKeyboardButton("↩️ Назад", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📍 *Моє місто*\n\n"
            "Ви ще не обрали своє місто.\n\n"
            "Оберіть місто, щоб швидко отримувати погоду для нього.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def show_region_cities(query, region, show_back_button=False):
    """Показати міста області"""
    # Знаходимо всі міста області
    cities_in_region = []
    for name, settlements_list in settlements_db.settlements.items():
        for settlement in settlements_list:
            if settlement['region'] == region:
                cities_in_region.append({
                    'name': name,
                    'population': settlement.get('population', 0),
                    'type': settlement['type']
                })
                break
    
    # Сортуємо за населенням
    cities_in_region.sort(key=lambda x: x['population'], reverse=True)
    
    # Формуємо список
    cities_list = ""
    for i, city in enumerate(cities_in_region[:15], 1):
        pop_str = f" ({city['population']:,} чол.)" if city['population'] > 0 else ""
        cities_list += f"{i}. {city['name']}{pop_str}\n"
    
    # Створюємо кнопки
    keyboard = []
    for city in cities_in_region[:6]:
        keyboard.append([InlineKeyboardButton(
            f"🌤 {city['name']}", 
            callback_data=f"weather_{city['name']}_{region}"
        )])
    
    if show_back_button:
        keyboard.append([
            InlineKeyboardButton("↩️ Назад", callback_data=f"weather_back_{region}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("🔍 Пошук", callback_data="search"),
            InlineKeyboardButton("↩️ Назад", callback_data="main_menu")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🏙 *Міста {region} області:*\n\n{cities_list}\n"
        f"Оберіть місто для отримання погоди:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def add_to_favorites(query, context, settlement_name, region):
    """Додати місто до улюблених"""
    user_id = query.from_user.id
    favorites = context.user_data.get('favorites', [])
    
    # Перевіряємо, чи вже є в улюблених
    for fav in favorites:
        if fav['name'] == settlement_name and fav['region'] == region:
            await query.answer("Це місто вже в улюблених!")
            return
    
    # Додаємо до улюблених
    favorites.append({
        'name': settlement_name,
        'region': region
    })
    context.user_data['favorites'] = favorites
    
    await query.answer(f"✅ {settlement_name} додано до улюблених!")
    
    # Показуємо оновлене повідомлення з погодою
    await process_weather_request(query, settlement_name, region)

async def clear_favorites(query, context):
    """Очистити улюблені міста"""
    context.user_data['favorites'] = []
    
    keyboard = [
        [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
        [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✅ *Улюблені міста очищено!*\n\n"
        "Список улюблених міст порожній.",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_settings_option(query, option):
    """Показати опцію налаштувань"""
    if option == "notifications":
        text = "🔔 *Сповіщення*\n\nНалаштування сповіщень ще в розробці."
    elif option == "theme":
        text = "🎨 *Тема*\n\nВибір теми ще в розробці."
    elif option == "units":
        text = "🌡 *Одиниці виміру*\n\nНалаштування одиниць виміру ще в розробці."
    else:
        text = "⚙️ *Налаштування*\n\nЦя опція ще в розробці."
    
    keyboard = [
        [InlineKeyboardButton("↩️ Назад", callback_data="settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def show_help(query):
    """Показати довідку"""
    help_text = (
        "ℹ️ *Довідка по боту*\n\n"
        "*Пошук населених пунктів:*\n"
        "1. Почніть вводити назву (мінімум 2 символи)\n"
        "2. Якщо є кілька пунктів з однаковою назвою - оберіть область\n"
        "3. Отримайте детальний прогноз погоди\n\n"
        "*Приклади запитів:*\n"
        "• 'ки' → Київ\n"
        "• 'нов' → покаже всі пункти, що починаються на 'нов'\n"
        "• 'первомайськ' → покаже обидва Первомайськи\n\n"
        "*Основні команди:*\n"
        "/start - головне меню\n"
        "/help - ця довідка\n"
        "/find [назва] - пошук населеного пункту\n"
        "/regions - список областей\n"
        "/stats - статистика бази даних\n"
        "/favorites - улюблені міста\n"
        "/settings - налаштування\n\n"
        "*Інформація про погоду:*\n"
        "• Температура повітря\n"
        "• Вітер на землі та висотах 400, 600, 800, 1000 м\n"
        "• Напрям вітру в градусах\n"
        "• Вологість повітря\n"
        "• Опади (дощ, сніг)\n"
        "• Нижня кромка хмар\n"
        "• Тиск\n"
        "• Видимість"
    )
    
    keyboard = [
        [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)

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
        
        # Додавання обробників команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("find", find_command))
        application.add_handler(CommandHandler("regions", regions_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("favorites", favorites_command))
        application.add_handler(CommandHandler("settings", settings_command))
        
        # Обробник кнопок
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Обробник текстових повідомлень
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Обробник помилок
        application.add_error_handler(error_handler)
        
        print("✅ Application created")
        print(f"✅ Database loaded: {len(settlements_db.settlements)} settlements")
        print("✅ Open-Meteo API: Ready")
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
    main()