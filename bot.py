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

# Додамо перевірку для веб-сервера
if __name__ == '__main__':
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
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
    print("✅ Libraries imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Імпорт власних модулів
from settlements_db import settlements_db
from weather_api import weather_api

# ============================================================================
# КЛАВІАТУРА МЕНЮ
# ============================================================================

def get_main_keyboard():
    """Отримати головну клавіатуру меню"""
    return ReplyKeyboardMarkup([
        [KeyboardButton("🌤 Поточна погода")],
        [KeyboardButton("📅 Прогноз на 3 дні")],
        [KeyboardButton("🔍 Пошук міста")],
        [KeyboardButton("🏙 Обласні центри")],
        [KeyboardButton("⭐️ Улюблені міста")],
        [KeyboardButton("📊 Статистика"), KeyboardButton("❓ Допомога")]
    ], resize_keyboard=True, persistent=True)

def get_back_keyboard():
    """Отримати клавіатуру з кнопкою Назад"""
    return ReplyKeyboardMarkup([
        [KeyboardButton("↩️ Назад до меню")]
    ], resize_keyboard=True, one_time_keyboard=True)

# ============================================================================
# ОБРОБНИКИ КОМАНД
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - головне меню"""
    user = update.effective_user
    
    welcome_text = (
        f"👋 Вітаю, {user.first_name}!\n\n"
        f"🇺🇦 *Український бот погоди*\n\n"
        f"🌤 *Доступні функції:*\n"
        f"• Пошук будь-якого населеного пункту України\n"
        f"• Детальна інформація про погоду\n"
        f"• Прогноз на 3 дні з почасовими даними\n"
        f"• Всі обласні центри України\n"
        f"• Збереження улюблених міст\n\n"
        f"📊 *База даних:* {len(settlements_db.settlements)} населених пунктів\n\n"
        f"👇 *Оберіть опцію з меню внизу:*"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = (
        "ℹ️ *Довідка по боту*\n\n"
        
        "🔍 *Пошук населених пунктів:*\n"
        "• Введіть назву або частину назви\n"
        "• Мінімум 2 символи\n"
        "• Якщо є кілька міст з однаковою назвою - оберіть область\n\n"
        
        "📅 *Прогноз на 3 дні:*\n"
        "• Детальний прогноз погоди\n"
        "• Температура мінімальна/максимальна\n"
        "• Опади та ймовірність опадів\n"
        "• Вітер та напрям вітру\n"
        "• Почасовий прогноз на сьогодні\n\n"
        
        "🏙 *Обласні центри:*\n"
        "• Всі 24 обласні центри України\n"
        "• Швидкий доступ до будь-якого центру\n\n"
        
        "⭐️ *Улюблені міста:*\n"
        "• Додавайте міста до улюблених\n"
        "• Швидкий доступ до погоди\n\n"
        
        "💡 *Поради:*\n"
        "• Використовуйте українську мову\n"
        "• Для точного пошуку вкажіть область\n"
        "• Наприклад: 'Новоград (Житомирська)'\n"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def handle_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка натискань кнопок меню"""
    text = update.message.text
    
    if text == "🌤 Поточна погода":
        await update.message.reply_text(
            "🔍 *Пошук для поточної погоди*\n\n"
            "Введіть назву населеного пункту:",
            parse_mode='Markdown',
            reply_markup=get_back_keyboard()
        )
        context.user_data['awaiting_city_for'] = 'current'
        
    elif text == "📅 Прогноз на 3 дні":
        await update.message.reply_text(
            "📅 *Пошук для прогнозу на 3 дні*\n\n"
            "Введіть назву населеного пункту:",
            parse_mode='Markdown',
            reply_markup=get_back_keyboard()
        )
        context.user_data['awaiting_city_for'] = 'forecast'
        
    elif text == "🔍 Пошук міста":
        await update.message.reply_text(
            "🔍 *Пошук населеного пункту*\n\n"
            "Введіть назву або частину назви (мінімум 2 символи):",
            parse_mode='Markdown',
            reply_markup=get_back_keyboard()
        )
        context.user_data['awaiting_city_for'] = 'search'
        
    elif text == "🏙 Обласні центри":
        await show_regional_centers(update, context)
        
    elif text == "⭐️ Улюблені міста":
        await show_favorites(update, context)
        
    elif text == "📊 Статистика":
        await show_statistics(update)
        
    elif text == "❓ Допомога":
        await help_command(update, context)
        
    elif text == "↩️ Назад до меню":
        await start_command(update, context)
        if 'awaiting_city_for' in context.user_data:
            del context.user_data['awaiting_city_for']

# ============================================================================
# ОБРОБКА ПОШУКУ
# ============================================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка текстових повідомлень"""
    text = update.message.text.strip()
    
    # Перевіряємо, чи це команда
    if text.startswith('/'):
        return
    
    # Перевіряємо, чи очікуємо введення міста
    if 'awaiting_city_for' in context.user_data:
        action = context.user_data['awaiting_city_for']
        
        if text == "↩️ Назад до меню":
            await start_command(update, context)
            del context.user_data['awaiting_city_for']
            return
        
        if len(text) < 2:
            await update.message.reply_text(
                "❌ *Занадто короткий запит.*\n\n"
                "Введіть мінімум 2 символи для пошуку.",
                parse_mode='Markdown',
                reply_markup=get_back_keyboard()
            )
            return
        
        # Пошук населених пунктів
        settlements = settlements_db.find_settlements_by_prefix(text, limit=20)
        
        if not settlements:
            await update.message.reply_text(
                f"❌ *Не знайдено населених пунктів за запитом '{text}'*\n\n"
                f"📝 *Поради:*\n"
                f"• Перевірте написання\n"
                f"• Спробуйте іншу частину назви\n" 
                f"• Використовуйте українську мову",
                parse_mode='Markdown',
                reply_markup=get_back_keyboard()
            )
            return
        
        # Якщо знайдено тільки один результат
        if len(settlements) == 1:
            settlement = settlements[0]
            if action == 'current':
                await process_current_weather(update, settlement['name'], settlement['region'])
            elif action == 'forecast':
                await process_3day_forecast(update, settlement['name'], settlement['region'])
            elif action == 'search':
                await process_current_weather(update, settlement['name'], settlement['region'])
            return
        
        # Якщо знайдено кілька результатів
        await show_search_results(update, settlements, action, context)
        return
    
    # Звичайний пошук (якщо не очікуємо спеціального введення)
    if len(text) >= 2:
        await handle_quick_search(update, text, context)
    else:
        await update.message.reply_text(
            "🤔 *Не розпізнано запит.*\n\n"
            "📝 *Формати запитів:*\n"
            "• Назва населеного пункту (напр. 'Київ')\n"
            "• Частина назви (напр. 'ки')\n"
            "• Назва з областю (напр. 'Новоград (Житомирська)')\n\n"
            "ℹ️ Мінімум 2 символи для пошуку",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

async def handle_quick_search(update: Update, query: str, context: ContextTypes.DEFAULT_TYPE):
    """Обробка швидкого пошуку"""
    settlements = settlements_db.find_settlements_by_prefix(query, limit=15)
    
    if not settlements:
        await update.message.reply_text(
            f"❌ *Не знайдено населених пунктів за запитом '{query}'*",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    
    if len(settlements) == 1:
        settlement = settlements[0]
        await process_current_weather(update, settlement['name'], settlement['region'])
        return
    
    # Показуємо результати пошуку
    message = f"🔍 *Знайдено {len(settlements)} населених пунктів:*\n\n"
    
    for i, settlement in enumerate(settlements[:10], 1):
        pop_str = f" ({settlement['population']:,} чол.)" if settlement['population'] > 0 else ""
        message += f"{i}. {settlement['name']} ({settlement['region']}){pop_str}\n"
    
    if len(settlements) > 10:
        message += f"\n... та ще {len(settlements) - 10} інших\n"
    
    message += "\n📝 *Введіть номер пункту або повну назву з областю*"
    
    # Зберігаємо результати пошуку
    context.user_data['last_search_results'] = settlements
    context.user_data['last_search_query'] = query
    
    keyboard = [
        [InlineKeyboardButton(f"{i}. {s['name']}", callback_data=f"city_{i}")]
        for i, s in enumerate(settlements[:5], 1)
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_search_results(update: Update, settlements: List[dict], action: str, context: ContextTypes.DEFAULT_TYPE):
    """Показати результати пошуку з інлайн-кнопками"""
    message = f"🔍 *Знайдено {len(settlements)} населених пунктів:*\n\n"
    
    for i, settlement in enumerate(settlements[:10], 1):
        pop_str = f" ({settlement['population']:,} чол.)" if settlement['population'] > 0 else ""
        message += f"{i}. {settlement['name']} ({settlement['region']}){pop_str}\n"
    
    if len(settlements) > 10:
        message += f"\n... та ще {len(settlements) - 10} інших\n"
    
    # Створюємо кнопки
    keyboard = []
    for i, settlement in enumerate(settlements[:5], 1):
        if action == 'current':
            callback_data = f"current_{i}"
        elif action == 'forecast':
            callback_data = f"forecast_{i}"
        else:
            callback_data = f"city_{i}"
        
        keyboard.append([InlineKeyboardButton(
            f"{i}. {settlement['name']}",
            callback_data=callback_data
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Зберігаємо результати
    context.user_data['last_search_results'] = settlements
    context.user_data['last_search_action'] = action
    
    await update.message.reply_text(
        message + "\n👇 *Оберіть пункт:*",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# ============================================================================
# ОБРОБНИКИ ІНЛАЙН-КНОПОК
# ============================================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка натискання інлайн-кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('current_'):
        index = int(data.split('_')[1]) - 1
        if 'last_search_results' in context.user_data:
            results = context.user_data['last_search_results']
            if 0 <= index < len(results):
                settlement = results[index]
                await process_current_weather(query, settlement['name'], settlement['region'])
    
    elif data.startswith('forecast_'):
        index = int(data.split('_')[1]) - 1
        if 'last_search_results' in context.user_data:
            results = context.user_data['last_search_results']
            if 0 <= index < len(results):
                settlement = results[index]
                await process_3day_forecast(query, settlement['name'], settlement['region'])
    
    elif data.startswith('city_'):
        index = int(data.split('_')[1]) - 1
        if 'last_search_results' in context.user_data:
            results = context.user_data['last_search_results']
            if 0 <= index < len(results):
                settlement = results[index]
                await process_current_weather(query, settlement['name'], settlement['region'])
    
    elif data.startswith('add_fav_'):
        parts = data.split('_')
        if len(parts) >= 3:
            city_index = int(parts[2]) - 1
            if 'last_search_results' in context.user_data:
                results = context.user_data['last_search_results']
                if 0 <= city_index < len(results):
                    settlement = results[city_index]
                    await add_to_favorites(query, context, settlement['name'], settlement['region'])
    
    elif data.startswith('remove_fav_'):
        parts = data.split('_')
        if len(parts) >= 3:
            fav_index = int(parts[2]) - 1
            favorites = context.user_data.get('favorites', [])
            if 0 <= fav_index < len(favorites):
                fav = favorites[fav_index]
                await remove_from_favorites(query, context, fav['name'], fav['region'])
    
    elif data == 'clear_favorites':
        await clear_favorites(query, context)
    
    elif data.startswith('region_'):
        index = int(data.split('_')[1]) - 1
        centers = settlements_db.get_regional_centers()
        if 0 <= index < len(centers):
            center = centers[index]
            await process_current_weather(query, center['name'], center['region'])

# ============================================================================
# ОБЛАСНІ ЦЕНТРИ
# ============================================================================

async def show_regional_centers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показати обласні центри"""
    centers = settlements_db.get_regional_centers()
    
    centers_text = "🏙 *Обласні центри України:*\n\n"
    for i, center in enumerate(centers, 1):
        centers_text += f"{i}. {center['name']} ({center['region']})\n"
    
    # Створюємо кнопки
    keyboard = []
    row = []
    for i, center in enumerate(centers, 1):
        button_text = f"{i}. {center['name']}"
        if len(button_text) > 20:
            button_text = f"{i}. {center['name'][:17]}..."
        
        row.append(InlineKeyboardButton(button_text, callback_data=f"region_{i}"))
        
        if len(row) == 2 or i == len(centers):
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'message'):
        await update.message.reply_text(
            centers_text + "\n👇 *Оберіть місто:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.edit_message_text(
            centers_text + "\n👇 *Оберіть місто:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

# ============================================================================
# УЛЮБЛЕНІ МІСТА
# ============================================================================

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показати улюблені міста"""
    favorites = context.user_data.get('favorites', [])
    
    if not favorites:
        if hasattr(update, 'message'):
            await update.message.reply_text(
                "⭐️ *Улюблені міста*\n\n"
                "У вас ще немає улюблених міст.\n\n"
                "Додайте місто до улюблених, щоб швидко отримувати погоду.",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
        else:
            await update.edit_message_text(
                "⭐️ *Улюблені міста*\n\n"
                "У вас ще немає улюблених міст.\n\n"
                "Додайте місто до улюблених, щоб швидко отримувати погоду.",
                parse_mode='Markdown'
            )
        return
    
    favorites_text = "⭐️ *Ваші улюблені міста:*\n\n"
    for i, fav in enumerate(favorites, 1):
        favorites_text += f"{i}. {fav['name']} ({fav['region']})\n"
    
    # Створюємо кнопки
    keyboard = []
    for i, fav in enumerate(favorites, 1):
        keyboard.append([
            InlineKeyboardButton(f"🌤 {fav['name']}", callback_data=f"current_{i}"),
            InlineKeyboardButton("🗑", callback_data=f"remove_fav_{i}")
        ])
    
    keyboard.append([InlineKeyboardButton("🗑 Очистити улюблені", callback_data="clear_favorites")])
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Зберігаємо список улюблених для callback
    context.user_data['last_search_results'] = favorites
    context.user_data['last_search_action'] = 'current'
    
    if hasattr(update, 'message'):
        await update.message.reply_text(
            favorites_text + "\n👇 *Оберіть місто:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.edit_message_text(
            favorites_text + "\n👇 *Оберіть місто:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def add_to_favorites(update, context, settlement_name, region):
    """Додати місто до улюблених"""
    favorites = context.user_data.get('favorites', [])
    
    # Перевіряємо, чи вже є в улюблених
    for fav in favorites:
        if fav['name'] == settlement_name and fav['region'] == region:
            if hasattr(update, 'answer'):
                await update.answer("✅ Це місто вже в улюблених!")
            return
    
    # Додаємо до улюблених
    favorites.append({
        'name': settlement_name,
        'region': region
    })
    context.user_data['favorites'] = favorites
    
    if hasattr(update, 'answer'):
        await update.answer(f"✅ {settlement_name} додано до улюблених!")
    
    # Показуємо оновлений список
    await show_favorites(update, context)

async def remove_from_favorites(update, context, settlement_name, region):
    """Видалити місто з улюблених"""
    favorites = context.user_data.get('favorites', [])
    
    # Шукаємо та видаляємо місто
    new_favorites = []
    for fav in favorites:
        if not (fav['name'] == settlement_name and fav['region'] == region):
            new_favorites.append(fav)
    
    context.user_data['favorites'] = new_favorites
    
    if hasattr(update, 'answer'):
        await update.answer(f"✅ {settlement_name} видалено з улюблених!")
    
    # Показуємо оновлений список
    await show_favorites(update, context)

async def clear_favorites(update, context):
    """Очистити улюблені міста"""
    context.user_data['favorites'] = []
    
    if hasattr(update, 'answer'):
        await update.answer("✅ Улюблені міста очищено!")
    
    await show_favorites(update, context)

# ============================================================================
# СТАТИСТИКА
# ============================================================================

async def show_statistics(update: Update):
    """Показати статистику"""
    stats = settlements_db.get_statistics()
    
    stats_text = f"📊 *Статистика бази даних:*\n\n"
    stats_text += f"• Унікальних назв: *{stats['unique_names']}*\n"
    stats_text += f"• Загальна кількість записів: *{stats['total_entries']}*\n"
    stats_text += f"• Областей: *{stats['regions_count']}*\n\n"
    
    stats_text += "*Топ-5 найбільших міст:*\n"
    for i, city in enumerate(stats['largest_cities'][:5], 1):
        stats_text += f"{i}. {city['name']} ({city['region']}): {city['population']:,} чол.\n"
    
    if hasattr(update, 'message'):
        await update.message.reply_text(
            stats_text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    else:
        await update.edit_message_text(
            stats_text,
            parse_mode='Markdown'
        )

# ============================================================================
# ОБРОБКА ПОГОДИ
# ============================================================================

async def process_current_weather(update: Update, settlement_name: str, region: str):
    """Обробка запиту про поточну погоду"""
    try:
        if hasattr(update, 'edit_message_text'):
            message = await update.edit_message_text(
                f"🔍 Отримую погоду для {settlement_name} ({region})...", 
                parse_mode='Markdown'
            )
        else:
            message = await update.message.reply_text(
                f"🔍 Отримую погоду для {settlement_name} ({region})...", 
                parse_mode='Markdown'
            )
        
        # Отримуємо координати
        lat, lon = settlements_db.get_coordinates(settlement_name, region)
        
        if not lat or not lon:
            error_msg = f"❌ Не знайдено координат для '{settlement_name}' ({region})"
            if hasattr(message, 'edit_text'):
                await message.edit_text(error_msg, parse_mode='Markdown')
            else:
                await update.reply_text(error_msg, parse_mode='Markdown')
            return
        
        # Отримуємо погоду
        weather_data = weather_api.get_weather(lat, lon, forecast_days=1)
        
        if not weather_data:
            error_text = (
                f"❌ Не вдалося отримати погоду для {settlement_name} ({region})\n\n"
                f"Можливі причини:\n"
                f"• Проблеми з підключенням\n"
                f"• Тимчасовий збій сервісу\n"
                f"• Спробуйте через хвилину"
            )
            if hasattr(message, 'edit_text'):
                await message.edit_text(error_text, parse_mode='Markdown')
            else:
                await update.reply_text(error_text, parse_mode='Markdown')
            return
        
        # Форматуємо повідомлення
        weather_text = weather_api.format_current_weather(settlement_name, region, weather_data)
        
        if not weather_text:
            error_text = f"❌ Помилка обробки даних для {settlement_name}"
            if hasattr(message, 'edit_text'):
                await message.edit_text(error_text, parse_mode='Markdown')
            else:
                await update.reply_text(error_text, parse_mode='Markdown')
            return
        
        # Створюємо кнопки дій
        keyboard = [
            [
                InlineKeyboardButton("📅 Прогноз на 3 дні", callback_data=f"forecast_city"),
                InlineKeyboardButton("⭐️ Додати до улюблених", callback_data=f"add_fav_{settlement_name}")
            ],
            [
                InlineKeyboardButton("🔄 Оновити", callback_data=f"refresh"),
                InlineKeyboardButton("🔍 Новий пошук", callback_data=f"new_search")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(message, 'edit_text'):
            await message.edit_text(weather_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.reply_text(weather_text, parse_mode='Markdown', reply_markup=reply_markup)
        
        logger.info(f"Weather sent for {settlement_name} ({region})")
            
    except Exception as e:
        logger.error(f"Error processing weather request: {e}")
        error_msg = "❌ Виникла критична помилка. Спробуйте пізніше."
        
        if hasattr(update, 'message'):
            await update.message.reply_text(error_msg, parse_mode='Markdown')
        elif hasattr(update, 'edit_message_text'):
            await update.edit_message_text(error_msg, parse_mode='Markdown')
        else:
            await update.reply_text(error_msg, parse_mode='Markdown')

async def process_3day_forecast(update: Update, settlement_name: str, region: str):
    """Обробка запиту про прогноз на 3 дні"""
    try:
        if hasattr(update, 'edit_message_text'):
            message = await update.edit_message_text(
                f"📅 Отримую прогноз для {settlement_name} ({region})...", 
                parse_mode='Markdown'
            )
        else:
            message = await update.message.reply_text(
                f"📅 Отримую прогноз для {settlement_name} ({region})...", 
                parse_mode='Markdown'
            )
        
        # Отримуємо координати
        lat, lon = settlements_db.get_coordinates(settlement_name, region)
        
        if not lat or not lon:
            error_msg = f"❌ Не знайдено координат для '{settlement_name}' ({region})"
            if hasattr(message, 'edit_text'):
                await message.edit_text(error_msg, parse_mode='Markdown')
            else:
                await update.reply_text(error_msg, parse_mode='Markdown')
            return
        
        # Отримуємо погоду з прогнозом на 3 дні
        weather_data = weather_api.get_weather(lat, lon, forecast_days=3)
        
        if not weather_data:
            error_text = (
                f"❌ Не вдалося отримати прогноз для {settlement_name} ({region})\n\n"
                f"Можливі причини:\n"
                f"• Проблеми з підключенням\n"
                f"• Тимчасовий збій сервісу\n"
                f"• Спробуйте через хвилину"
            )
            if hasattr(message, 'edit_text'):
                await message.edit_text(error_text, parse_mode='Markdown')
            else:
                await update.reply_text(error_text, parse_mode='Markdown')
            return
        
        # Отримуємо 3 повідомлення з прогнозом
        forecast_messages = weather_api.format_3day_forecast(settlement_name, region, weather_data)
        
        if not forecast_messages:
            error_text = f"❌ Помилка обробки прогнозу для {settlement_name}"
            if hasattr(message, 'edit_text'):
                await message.edit_text(error_text, parse_mode='Markdown')
            else:
                await update.reply_text(error_text, parse_mode='Markdown')
            return
        
        # Надсилаємо кожне повідомлення окремо
        for i, forecast_text in enumerate(forecast_messages):
            if i == 0:
                # Перше повідомлення
                if hasattr(message, 'edit_text'):
                    await message.edit_text(forecast_text, parse_mode='Markdown')
                else:
                    await update.reply_text(forecast_text, parse_mode='Markdown')
            else:
                # Інші повідомлення
                await update.reply_text(forecast_text, parse_mode='Markdown')
        
        # Додаємо кнопки під останнім повідомленням
        keyboard = [
            [
                InlineKeyboardButton("🌤 Поточна погода", callback_data=f"current_city"),
                InlineKeyboardButton("⭐️ Додати до улюблених", callback_data=f"add_fav_{settlement_name}")
            ],
            [
                InlineKeyboardButton("🔍 Новий пошук", callback_data=f"new_search"),
                InlineKeyboardButton("↩️ Меню", callback_data=f"back_to_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Надсилаємо повідомлення з кнопками
        await update.reply_text(
            "👇 *Оберіть дію:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        logger.info(f"3-day forecast sent for {settlement_name} ({region})")
            
    except Exception as e:
        logger.error(f"Error processing forecast request: {e}")
        error_msg = "❌ Виникла критична помилка. Спробуйте пізніше."
        
        if hasattr(update, 'message'):
            await update.message.reply_text(error_msg, parse_mode='Markdown')
        elif hasattr(update, 'edit_message_text'):
            await update.edit_message_text(error_msg, parse_mode='Markdown')
        else:
            await update.reply_text(error_msg, parse_mode='Markdown')

# ============================================================================
# ОБРОБНИК ПОМИЛОК
# ============================================================================

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
        
        # Обробник кнопок меню
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(🌤|📅|🔍|🏙|⭐️|📊|❓|↩️)'), handle_menu_button))
        
        # Обробник інлайн-кнопок
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