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
from weather_api import weather_api

# ============================================================================
# ОБРОБНИКИ КОМАНД
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - головне меню"""
    user = update.effective_user
    
    # Основний клавіатура меню
    keyboard = [
        [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
        [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
        [InlineKeyboardButton("📅 Прогноз на 3 дні", callback_data="forecast_3days")],
        [InlineKeyboardButton("⭐️ Улюблені міста", callback_data="favorites")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("❓ Допомога", callback_data="help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
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
        f"👇 *Оберіть опцію з меню:*"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
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
        
        "📊 *Статистика:*\n"
        "• Інформація про базу даних\n"
        "• Найбільші міста України\n\n"
        
        "💡 *Поради:*\n"
        "• Використовуйте українську мову\n"
        "• Для точного пошуку вкажіть область\n"
        "• Наприклад: 'Новоград (Житомирська)'\n\n"
        
        "✏️ *Приклади запитів:*\n"
        "/find ки\n"
        "/find нов\n"
        "/find первомайськ\n"
        "або просто напишіть назву міста"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
        [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
        [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /find - пошук населеного пункту"""
    if not context.args:
        keyboard = [
            [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
            [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔍 *Пошук населеного пункту*\n\n"
            "Використання: /find [назва або частина назви]\n\n"
            "*Приклади:*\n"
            "/find ки\n"
            "/find нов\n"
            "/find первомайськ\n\n"
            "📝 *Порада:* Мінімум 2 символи",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    search_query = ' '.join(context.args)
    await search_settlements(update, search_query, context)

async def regions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /regions - список областей України"""
    await show_regional_centers_menu(update)

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
    
    keyboard = [
        [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
        [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
        [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /favorites - улюблені міста"""
    await show_favorites_menu(update, context)

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
            [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
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
# МЕНЮ ТА КНОПКИ
# ============================================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка натискання кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "main_menu":
        await show_main_menu(query)
    
    elif data == "search":
        await show_search_menu(query)
    
    elif data == "regional_centers":
        await show_regional_centers_menu(query)
    
    elif data == "forecast_3days":
        await show_forecast_menu(query, context)
    
    elif data == "favorites":
        await show_favorites_menu(query, context)
    
    elif data == "stats":
        await show_stats_menu(query)
    
    elif data == "help":
        await show_help_menu(query)
    
    elif data.startswith("weather_"):
        parts = data.split('_')
        if len(parts) >= 3:
            settlement_name = parts[1]
            region = '_'.join(parts[2:])
            await process_weather_request(query, settlement_name, region)
    
    elif data.startswith("forecast_city_"):
        parts = data.split('_')
        if len(parts) >= 4:
            settlement_name = parts[2]
            region = '_'.join(parts[3:])
            await process_forecast_request(query, settlement_name, region)
    
    elif data.startswith("region_center_"):
        parts = data.split('_')
        if len(parts) >= 4:
            settlement_name = parts[2]
            region = '_'.join(parts[3:])
            await process_weather_request(query, settlement_name, region)
    
    elif data.startswith("add_fav_"):
        parts = data.split('_')
        if len(parts) >= 4:
            settlement_name = parts[2]
            region = '_'.join(parts[3:])
            await add_to_favorites(query, context, settlement_name, region)
    
    elif data.startswith("remove_fav_"):
        parts = data.split('_')
        if len(parts) >= 4:
            settlement_name = parts[2]
            region = '_'.join(parts[3:])
            await remove_from_favorites(query, context, settlement_name, region)
    
    elif data == "clear_favorites":
        await clear_favorites(query, context)

async def show_main_menu(query):
    """Показати головне меню"""
    keyboard = [
        [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
        [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
        [InlineKeyboardButton("📅 Прогноз на 3 дні", callback_data="forecast_3days")],
        [InlineKeyboardButton("⭐️ Улюблені міста", callback_data="favorites")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("❓ Допомога", callback_data="help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🇺🇦 *Український бот погоди*\n\n"
        "👇 *Оберіть опцію з меню:*",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_search_menu(query):
    """Показати меню пошуку"""
    keyboard = [
        [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
        [InlineKeyboardButton("⭐️ Улюблені міста", callback_data="favorites")],
        [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔍 *Пошук населеного пункту*\n\n"
        "Введіть назву або частину назви:\n\n"
        "*Приклади:*\n"
        "• Київ\n"
        "• ки\n"
        "• нов\n"
        "• Первомайськ (Миколаївська)\n\n"
        "📝 Мінімум 2 символи",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_regional_centers_menu(update):
    """Показати меню обласних центрів"""
    centers = settlements_db.get_regional_centers()
    
    # Групуємо центри по 2 в рядку
    keyboard = []
    row = []
    
    for i, center in enumerate(centers):
        button_text = f"🏙 {center['name']}"
        if len(button_text) > 20:  # Обмежуємо довжину тексту
            button_text = f"🏙 {center['name'][:15]}..."
        
        row.append(InlineKeyboardButton(
            button_text,
            callback_data=f"region_center_{center['name']}_{center['region']}"
        ))
        
        if len(row) == 2 or i == len(centers) - 1:
            keyboard.append(row)
            row = []
    
    # Додаємо кнопки навігації
    keyboard.append([
        InlineKeyboardButton("🔍 Пошук міста", callback_data="search"),
        InlineKeyboardButton("📅 Прогноз на 3 дні", callback_data="forecast_3days")
    ])
    keyboard.append([
        InlineKeyboardButton("⭐️ Улюблені міста", callback_data="favorites"),
        InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    centers_text = "*Обласні центри України:*\n\n"
    for center in centers:
        centers_text += f"• {center['name']} ({center['region']})\n"
    
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

async def show_forecast_menu(query, context):
    """Показати меню прогнозу"""
    # Перевіряємо, чи є останній пошук
    if 'last_search_results' in context.user_data:
        results = context.user_data['last_search_results']
        
        keyboard = []
        for i, settlement in enumerate(results[:5]):
            keyboard.append([InlineKeyboardButton(
                f"📅 {settlement['name']} ({settlement['region']})",
                callback_data=f"forecast_city_{settlement['name']}_{settlement['region']}"
            )])
        
        keyboard.append([
            InlineKeyboardButton("🔍 Новий пошук", callback_data="search"),
            InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📅 *Прогноз на 3 дні*\n\n"
            "Оберіть місто з останнього пошуку або введіть назву нового міста:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
            [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
            [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📅 *Прогноз на 3 дні*\n\n"
            "Введіть назву міста для отримання прогнозу на 3 дні.\n\n"
            "📝 *Приклади:*\n"
            "• Київ\n"
            "• Одеса\n"
            "• Львів\n\n"
            "або оберіть місто з меню:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def show_favorites_menu(update, context):
    """Показати меню улюблених міст"""
    user_id = update.from_user.id if hasattr(update, 'from_user') else update.effective_user.id
    favorites = context.user_data.get('favorites', [])
    
    if not favorites:
        keyboard = [
            [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
            [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
            [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'message'):
            await update.message.reply_text(
                "⭐️ *Улюблені міста*\n\n"
                "У вас ще немає улюблених міст.\n\n"
                "Додайте місто до улюблених, щоб швидко отримувати погоду.",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.edit_message_text(
                "⭐️ *Улюблені міста*\n\n"
                "У вас ще немає улюблених міст.\n\n"
                "Додайте місто до улюблених, щоб швидко отримувати погоду.",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        return
    
    keyboard = []
    for fav in favorites:
        keyboard.append([
            InlineKeyboardButton(
                f"🌤 {fav['name']} ({fav['region']})",
                callback_data=f"weather_{fav['name']}_{fav['region']}"
            ),
            InlineKeyboardButton(
                "🗑",
                callback_data=f"remove_fav_{fav['name']}_{fav['region']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("🗑 Очистити улюблені", callback_data="clear_favorites"),
        InlineKeyboardButton("🔍 Додати ще", callback_data="search")
    ])
    keyboard.append([
        InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    favorites_text = "⭐️ *Ваші улюблені міста:*\n\n"
    for i, fav in enumerate(favorites, 1):
        favorites_text += f"{i}. {fav['name']} ({fav['region']})\n"
    
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

async def show_stats_menu(query):
    """Показати меню статистики"""
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
        [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
        [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_help_menu(query):
    """Показати меню довідки"""
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
    
    keyboard = [
        [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
        [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
        [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# ============================================================================
# ОБРОБКА ПОШУКУ ТА ПОГОДИ
# ============================================================================

async def search_settlements(update: Update, query: str, context: Optional[ContextTypes.DEFAULT_TYPE] = None):
    """Пошук населених пунктів"""
    if len(query) < 2:
        if hasattr(update, 'message'):
            await update.message.reply_text(
                "❌ *Занадто короткий запит.*\n\n"
                "Введіть мінімум 2 символи для пошуку.",
                parse_mode='Markdown'
            )
        else:
            await update.edit_message_text(
                "❌ *Занадто короткий запит.*\n\n"
                "Введіть мінімум 2 символи для пошуку.",
                parse_mode='Markdown'
            )
        return
    
    settlements = settlements_db.find_settlements_by_prefix(query, limit=15)
    
    if not settlements:
        keyboard = [
            [InlineKeyboardButton("🏙 Обласні центри", callback_data="regional_centers")],
            [InlineKeyboardButton("❓ Допомога", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'message'):
            await update.message.reply_text(
                f"❌ *Не знайдено населених пунктів за запитом '{query}'*\n\n"
                f"📝 *Поради:*\n"
                f"• Перевірте написання\n"
                f"• Спробуйте іншу частину назви\n" 
                f"• Використовуйте українську мову",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.edit_message_text(
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
    
    # Формуємо список
    for i, settlement in enumerate(settlements[:15], 1):
        pop_str = f" ({settlement['population']:,} чол.)" if settlement['population'] > 0 else ""
        message += f"{i}. {settlement['name']} ({settlement['region']}){pop_str}\n"
    
    message += "\n📝 *Виберіть номер пункту або напишіть повну назву з вказанням області*"
    
    # Зберігаємо результати пошуку в контексті
    if context and hasattr(update, 'message'):
        context.user_data['last_search_results'] = settlements
        context.user_data['last_search_query'] = query
    
    keyboard = [
        [InlineKeyboardButton("📅 Прогноз на 3 дні", callback_data="forecast_3days")],
        [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if hasattr(update, 'message'):
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def process_weather_request(update: Update, settlement_name: str, region: str):
    """Обробка запиту про поточну погоду"""
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
        weather_data = weather_api.get_weather(lat, lon, forecast_days=1)
        
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
        weather_text = weather_api.format_current_weather(settlement_name, region, weather_data)
        
        if not weather_text:
            error_text = f"❌ Помилка обробки даних для {settlement_name}"
            await message.edit_text(error_text, parse_mode='Markdown')
            return
        
        # Додаємо кнопки дій
        keyboard = [
            [
                InlineKeyboardButton("⭐️ Додати до улюблених", callback_data=f"add_fav_{settlement_name}_{region}"),
                InlineKeyboardButton("📅 Прогноз на 3 дні", callback_data=f"forecast_city_{settlement_name}_{region}")
            ],
            [
                InlineKeyboardButton("🔄 Оновити", callback_data=f"weather_{settlement_name}_{region}"),
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

async def process_forecast_request(update: Update, settlement_name: str, region: str):
    """Обробка запиту про прогноз на 3 дні"""
    try:
        # Повідомлення про завантаження
        if hasattr(update, 'message'):
            message = await update.message.reply_text(
                f"📅 Отримую прогноз для {settlement_name} ({region})...", 
                parse_mode='Markdown'
            )
        else:
            message = await update.edit_message_text(
                f"📅 Отримую прогноз для {settlement_name} ({region})...", 
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
            await message.edit_text(error_text, parse_mode='Markdown')
            return
        
        # Отримуємо 3 повідомлення з прогнозом
        forecast_messages = weather_api.format_3day_forecast(settlement_name, region, weather_data)
        
        if not forecast_messages:
            error_text = f"❌ Помилка обробки прогнозу для {settlement_name}"
            await message.edit_text(error_text, parse_mode='Markdown')
            return
        
        # Надсилаємо кожне повідомлення окремо
        for i, forecast_text in enumerate(forecast_messages):
            if i == 0:
                # Перше повідомлення - редагуємо оригінальне
                await message.edit_text(forecast_text, parse_mode='Markdown')
            else:
                # Інші повідомлення - надсилаємо нові
                if hasattr(update, 'message'):
                    await update.message.reply_text(forecast_text, parse_mode='Markdown')
                else:
                    # Якщо це callback query, надсилаємо нове повідомлення
                    await update.message.reply_text(forecast_text, parse_mode='Markdown')
        
        # Додаємо кнопки під останнім повідомленням
        keyboard = [
            [
                InlineKeyboardButton("🌤 Поточна погода", callback_data=f"weather_{settlement_name}_{region}"),
                InlineKeyboardButton("⭐️ Додати до улюблених", callback_data=f"add_fav_{settlement_name}_{region}")
            ],
            [
                InlineKeyboardButton("🔍 Новий пошук", callback_data="search"),
                InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Редагуємо останнє повідомлення, щоб додати кнопки
        if hasattr(update, 'message'):
            await update.message.reply_text(
                "👇 *Оберіть дію:*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
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
        else:
            await update.edit_message_text(error_msg, parse_mode='Markdown')

# ============================================================================
# УЛЮБЛЕНІ МІСТА
# ============================================================================

async def add_to_favorites(update, context, settlement_name, region):
    """Додати місто до улюблених"""
    user_id = update.from_user.id if hasattr(update, 'from_user') else update.effective_user.id
    favorites = context.user_data.get('favorites', [])
    
    # Перевіряємо, чи вже є в улюблених
    for fav in favorites:
        if fav['name'] == settlement_name and fav['region'] == region:
            await update.answer("✅ Це місто вже в улюблених!")
            return
    
    # Додаємо до улюблених
    favorites.append({
        'name': settlement_name,
        'region': region
    })
    context.user_data['favorites'] = favorites
    
    await update.answer(f"✅ {settlement_name} додано до улюблених!")

async def remove_from_favorites(update, context, settlement_name, region):
    """Видалити місто з улюблених"""
    user_id = update.from_user.id if hasattr(update, 'from_user') else update.effective_user.id
    favorites = context.user_data.get('favorites', [])
    
    # Шукаємо та видаляємо місто
    new_favorites = []
    for fav in favorites:
        if not (fav['name'] == settlement_name and fav['region'] == region):
            new_favorites.append(fav)
    
    context.user_data['favorites'] = new_favorites
    
    await update.answer(f"✅ {settlement_name} видалено з улюблених!")
    await show_favorites_menu(update, context)

async def clear_favorites(update, context):
    """Очистити улюблені міста"""
    context.user_data['favorites'] = []
    
    keyboard = [
        [InlineKeyboardButton("🔍 Пошук міста", callback_data="search")],
        [InlineKeyboardButton("↩️ Головне меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.edit_message_text(
        "✅ *Улюблені міста очищено!*\n\n"
        "Список улюблених міст порожній.",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

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
        application.add_handler(CommandHandler("find", find_command))
        application.add_handler(CommandHandler("regions", regions_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("favorites", favorites_command))
        
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