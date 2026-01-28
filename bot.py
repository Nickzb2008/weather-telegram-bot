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
    ], resize_keyboard=True)

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
        # Додаємо логування
        logger.info("Showing favorites menu")
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
                await process_current_weather(update, context, settlement['name'], settlement['region'])
            elif action == 'forecast':
                await process_3day_forecast(update, context, settlement['name'], settlement['region'])
            elif action == 'search':
                await process_current_weather(update, context, settlement['name'], settlement['region'])
            return
        
        # Якщо знайдено кілька результатів
        await show_search_results(update, context, settlements, action)
        return
    
    # Звичайний пошук (якщо не очікуємо спеціального введення)
    if len(text) >= 2:
        await handle_quick_search(update, context, text)
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

async def handle_quick_search(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
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
        await process_current_weather(update, context, settlement['name'], settlement['region'])
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
    
    # Створюємо інлайн-кнопки
    keyboard = []
    for i, settlement in enumerate(settlements[:5], 1):
        button_text = f"{i}. {settlement['name']}"
        if len(button_text) > 20:  # Обмеження Telegram
            button_text = f"{i}. {settlement['name'][:17]}..."
        
        callback_data = f"city_{i}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE, settlements: List[dict], action: str):
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
        button_text = f"{i}. {settlement['name']}"
        if len(button_text) > 20:
            button_text = f"{i}. {settlement['name'][:17]}..."
        
        if action == 'current':
            callback_data = f"current_{i}"
        elif action == 'forecast':
            callback_data = f"forecast_{i}"
        else:
            callback_data = f"city_{i}"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
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

async def test_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестова команда для перевірки улюблених"""
    # Додаємо тестове місто
    context.user_data['favorites'] = [
        {'name': 'Київ', 'region': 'Київська'},
        {'name': 'Львів', 'region': 'Львівська'},
        {'name': 'Одеса', 'region': 'Одеська'}
    ]
    
    await update.message.reply_text(
        "✅ Тестові міста додані до улюблених!",
        parse_mode='Markdown'
    )
    
    # Показуємо улюблені
    await show_favorites(update, context)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка натискання інлайн-кнопок"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # ВИПРАВЛЕНО: Обробка основних кнопок
    if data.startswith('current_'):
        try:
            if data == 'current_city':
                # Обробляємо випадок з улюблених міст
                favorites = context.user_data.get('favorites', [])
                if favorites:
                    # Створюємо імітацію update з callback_query
                    from telegram import Update
                    fake_update = Update(update_id=update.update_id, callback_query=query)
                    await process_current_weather(fake_update, context, favorites[0]['name'], favorites[0]['region'])
                else:
                    await query.answer("❌ У вас немає улюблених міст")
            else:
                index = int(data.split('_')[1]) - 1
                if 'last_search_results' in context.user_data:
                    results = context.user_data['last_search_results']
                    if 0 <= index < len(results):
                        settlement = results[index]
                        from telegram import Update
                        fake_update = Update(update_id=update.update_id, callback_query=query)
                        await process_current_weather(fake_update, context, settlement['name'], settlement['region'])
                    else:
                        await query.answer("❌ Результати пошуку не знайдено")
                else:
                    await query.answer("❌ Спочатку виконайте пошук")
        except (ValueError, IndexError) as e:
            logger.error(f"Error processing current button: {e}")
            await query.answer("❌ Помилка обробки запиту")
    
    elif data.startswith('forecast_'):
        try:
            if data == 'forecast_city':
                # Отримуємо останнє місто з контексту
                if 'last_city' in context.user_data and 'last_region' in context.user_data:
                    city = context.user_data['last_city']
                    region = context.user_data['last_region']
                    from telegram import Update
                    fake_update = Update(update_id=update.update_id, callback_query=query)
                    await process_3day_forecast(fake_update, context, city, region)
                else:
                    await query.answer("❌ Спочатку знайдіть місто для прогнозу")
            else:
                index = int(data.split('_')[1]) - 1
                if 'last_search_results' in context.user_data:
                    results = context.user_data['last_search_results']
                    if 0 <= index < len(results):
                        settlement = results[index]
                        from telegram import Update
                        fake_update = Update(update_id=update.update_id, callback_query=query)
                        await process_3day_forecast(fake_update, context, settlement['name'], settlement['region'])
                    else:
                        await query.answer("❌ Результати пошуку не знайдено")
                else:
                    await query.answer("❌ Спочатку виконайте пошук")
        except (ValueError, IndexError) as e:
            logger.error(f"Error processing forecast button: {e}")
            await query.answer("❌ Помилка обробки запиту")

    elif data.startswith('city_'):
        try:
            index = int(data.split('_')[1]) - 1
            if 'last_search_results' in context.user_data:
                results = context.user_data['last_search_results']
                if 0 <= index < len(results):
                    settlement = results[index]
                    from telegram import Update
                    fake_update = Update(update_id=update.update_id, callback_query=query)
                    await process_current_weather(fake_update, context, settlement['name'], settlement['region'])
                else:
                    await query.answer("❌ Результати пошуку не знайдено")
            else:
                await query.answer("❌ Спочатку виконайте пошук")
        except (ValueError, IndexError) as e:
            logger.error(f"Error processing city button: {e}")
            await query.answer("❌ Помилка обробки запиту")
    
    # Додаємо в улюблені
    elif data == 'add_fav':
        try:
            # Отримуємо останнє місто з контексту
            if 'last_city' in context.user_data and 'last_region' in context.user_data:
                settlement_name = context.user_data['last_city']
                region = context.user_data['last_region']
                
                # Додаємо логування для перевірки
                logger.info(f"Adding to favorites: {settlement_name} ({region})")
                
                # Перевіряємо, чи вже є в улюблених
                favorites = context.user_data.get('favorites', [])
                
                # Додаємо логування поточного списку
                logger.info(f"Current favorites: {favorites}")
                
                for fav in favorites:
                    if fav['name'] == settlement_name and fav['region'] == region:
                        await query.answer("✅ Це місто вже в улюблених!")
                        return
                
                # Додаємо до улюблених
                favorites.append({
                    'name': settlement_name,
                    'region': region
                })
                context.user_data['favorites'] = favorites
                
                # Логування оновленого списку
                logger.info(f"Updated favorites: {favorites}")
                
                await query.answer(f"✅ {settlement_name} додано до улюблених!")
            else:
                logger.error("No last_city or last_region in context")
                await query.answer("❌ Не вдалося додати до улюблених. Спочатку знайдіть місто.")
        except Exception as e:
            logger.error(f"Error adding to favorites: {e}", exc_info=True)
            await query.answer("❌ Помилка додавання до улюблених")

    # Видалення з улюблених
    elif data.startswith('remove_fav_'):
        try:
            parts = data.split('_')
            fav_index = int(parts[2]) - 1
            favorites = context.user_data.get('favorites', [])
            if 0 <= fav_index < len(favorites):
                fav = favorites[fav_index]
                # Шукаємо та видаляємо місто
                new_favorites = []
                removed = False
                for favorite in favorites:
                    if not (favorite['name'] == fav['name'] and favorite['region'] == fav['region']):
                        new_favorites.append(favorite)
                    else:
                        removed = True
                
                context.user_data['favorites'] = new_favorites
                
                if removed:
                    await query.answer(f"✅ {fav['name']} видалено з улюблених!")
                    # Показуємо оновлений список
                    await show_favorites(query, context)
                else:
                    await query.answer("❌ Місто не знайдено в улюблених")
            else:
                await query.answer("❌ Неправильний індекс улюбленого")
        except (ValueError, IndexError) as e:
            logger.error(f"Error removing from favorites: {e}")
            await query.answer("❌ Помилка при видаленні з улюблених")
    
    # Очищення улюблених
    elif data == 'clear_favorites':
        try:
            favorites = context.user_data.get('favorites', [])
            if favorites:
                context.user_data['favorites'] = []
                await query.answer("✅ Улюблені міста очищено!")
                # Показуємо порожній список
                await show_favorites(query, context)
            else:
                await query.answer("✅ Улюблених міст і так немає")
        except Exception as e:
            logger.error(f"Error clearing favorites: {e}")
            await query.answer("❌ Помилка очищення улюблених")
    
    # Обласні центри
    elif data.startswith('region_'):
        try:
            index = int(data.split('_')[1]) - 1
            centers = settlements_db.get_regional_centers()
            if 0 <= index < len(centers):
                center = centers[index]
                from telegram import Update
                fake_update = Update(update_id=update.update_id, callback_query=query)
                await process_current_weather(fake_update, context, center['name'], center['region'])
            else:
                await query.answer("❌ Неправильний індекс обласного центру")
        except (ValueError, IndexError) as e:
            logger.error(f"Error processing region button: {e}")
            await query.answer("❌ Помилка обробки запиту")
    
    # Назад до меню
    elif data == 'back_to_menu':
        try:
            user = query.from_user
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
            
            await query.edit_message_text(
                welcome_text,
                parse_mode='Markdown'
            )
            
            # Відправляємо нове повідомлення з клавіатурою
            await query.message.reply_text(
                "Оберіть опцію:",
                reply_markup=get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Error going back to menu: {e}")
            await query.answer("❌ Помилка повернення до меню")
    
    # Новий пошук
    elif data == 'new_search':
        try:
            await query.edit_message_text(
                "🔍 *Введіть назву населеного пункту для пошуку:*",
                parse_mode='Markdown'
            )
            # Встановлюємо прапор, що очікуємо введення міста
            context.user_data['awaiting_city_for'] = 'search'
            # Відправляємо клавіатуру з кнопкою Назад
            await query.message.reply_text(
                "Або натисніть кнопку Назад:",
                reply_markup=get_back_keyboard()
            )
        except Exception as e:
            logger.error(f"Error starting new search: {e}")
            await query.answer("❌ Помилка початку нового пошуку")
    
    # Оновлення погоди
    elif data == 'refresh':
        try:
            if 'last_city' in context.user_data:
                city = context.user_data['last_city']
                region = context.user_data.get('last_region', '')
                from telegram import Update
                fake_update = Update(update_id=update.update_id, callback_query=query)
                await process_current_weather(fake_update, context, city, region)
            else:
                await query.answer("❌ Немає даних для оновлення. Спочатку знайдіть місто.")
        except Exception as e:
            logger.error(f"Error refreshing weather: {e}")
            await query.answer("❌ Помилка оновлення погоди")
    
    else:
        logger.warning(f"Unrecognized callback data: {data}")
        await query.answer("❌ Дія не розпізнана")

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
    for i, center in enumerate(centers, 1):
        button_text = f"{i}. {center['name']}"
        if len(button_text) > 20:
            button_text = f"{i}. {center['name'][:17]}..."
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"region_{i}")])
    
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
        # Якщо немає улюблених
        if hasattr(update, 'message'):
            await update.message.reply_text(
                "⭐️ *Улюблені міста*\n\n"
                "У вас ще немає улюблених міст.\n\n"
                "Додайте місто до улюблених, щоб швидко отримувати погоду.",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
        elif hasattr(update, 'edit_message_text'):
            # Якщо це callback query
            await update.edit_message_text(
                "⭐️ *Улюблені міста*\n\n"
                "У вас ще немає улюблених міст.\n\n"
                "Додайте місто до улюблених, щоб швидко отримувати погоду.",
                parse_mode='Markdown'
            )
        return
    
    # Формуємо текст з улюбленими містами
    favorites_text = "⭐️ *Ваші улюблені міста:*\n\n"
    for i, fav in enumerate(favorites, 1):
        favorites_text += f"{i}. {fav['name']} ({fav['region']})\n"
    
    # Створюємо кнопки
    keyboard = []
    for i, fav in enumerate(favorites, 1):
        row = [
            InlineKeyboardButton(f"🌤 {fav['name']}", callback_data=f"current_{i}"),
            InlineKeyboardButton("🗑", callback_data=f"remove_fav_{i}")
        ]
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🗑 Очистити улюблені", callback_data="clear_favorites")])
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Зберігаємо список улюблених для callback
    context.user_data['last_search_results'] = favorites
    context.user_data['last_search_action'] = 'current'
    
    # Відправляємо повідомлення
    if hasattr(update, 'message'):
        await update.message.reply_text(
            favorites_text + "\n👇 *Оберіть місто:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    elif hasattr(update, 'edit_message_text'):
        # Якщо це callback query
        await update.edit_message_text(
            favorites_text + "\n👇 *Оберіть місто:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        # Якщо це просто query (з button_handler)
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
    
    # Зберігаємо останнє місто для кнопки "Додати до улюблених"
    context.user_data['last_city'] = settlement_name
    context.user_data['last_region'] = region
    
    if hasattr(update, 'answer'):
        await update.answer(f"✅ {settlement_name} додано до улюблених!")
    
    # Показуємо оновлений список
    await show_favorites(update, context)

async def remove_from_favorites(update, context, settlement_name, region):
    """Видалити місто з улюблених"""
    favorites = context.user_data.get('favorites', [])
    
    # Шукаємо та видаляємо місто
    new_favorites = []
    removed = False
    for fav in favorites:
        if not (fav['name'] == settlement_name and fav['region'] == region):
            new_favorites.append(fav)
        else:
            removed = True
    
    context.user_data['favorites'] = new_favorites
    
    if hasattr(update, 'answer'):
        if removed:
            await update.answer(f"✅ {settlement_name} видалено з улюблених!")
        else:
            await update.answer("❌ Місто не знайдено в улюблених")
    
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

async def process_current_weather(update: Update, context: ContextTypes.DEFAULT_TYPE, settlement_name: str, region: str):
    """Обробка запиту про поточну погоду"""
    try:
        # Зберігаємо останнє місто для кнопки "Додати до улюблених"
        context.user_data['last_city'] = settlement_name
        context.user_data['last_region'] = region
        
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
                InlineKeyboardButton("📅 Прогноз на 3 дні", callback_data="forecast_city"),
                InlineKeyboardButton("⭐️ Додати до улюблених", callback_data="add_fav")
            ],
            [
                InlineKeyboardButton("🔄 Оновити", callback_data="refresh"),
                InlineKeyboardButton("🔍 Новий пошук", callback_data="new_search")
            ],
            [
                InlineKeyboardButton("↩️ Меню", callback_data="back_to_menu")
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

async def process_3day_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE, settlement_name: str, region: str):
    """Обробка запиту про прогноз на 3 дні"""
    logger.info(f"Starting 3-day forecast for {settlement_name} ({region})")
    
    try:
        # ВИПРАВЛЕНО: Визначаємо, чи це callback_query або звичайне повідомлення
        is_callback = hasattr(update, 'callback_query')
        logger.info(f"Is callback: {is_callback}")
        
        if is_callback:
            # Якщо це callback від інлайн-кнопки
            query = update.callback_query
            logger.info(f"Editing message for callback")
            await query.edit_message_text(
                f"📅 Отримую прогноз для {settlement_name} ({region})...", 
                parse_mode='Markdown'
            )
            message_to_edit = query.message
        else:
            # Якщо це звичайне повідомлення
            logger.info(f"Sending new message")
            message = await update.message.reply_text(
                f"📅 Отримую прогноз для {settlement_name} ({region})...", 
                parse_mode='Markdown'
            )
            message_to_edit = message
        
        # Зберігаємо останнє місто для кнопки "Додати до улюблених"
        context.user_data['last_city'] = settlement_name
        context.user_data['last_region'] = region
        
        # Отримуємо координати
        lat, lon = settlements_db.get_coordinates(settlement_name, region)
        logger.info(f"Coordinates: {lat}, {lon}")
        
        if not lat or not lon:
            error_msg = f"❌ Не знайдено координат для '{settlement_name}' ({region})"
            logger.error(error_msg)
            if is_callback:
                await update.callback_query.edit_message_text(error_msg, parse_mode='Markdown')
            else:
                await update.message.reply_text(error_msg, parse_mode='Markdown')
            return
        
        # Отримуємо погоду з прогнозом на 3 дні
        logger.info("Getting weather data from API...")
        weather_data = weather_api.get_weather(lat, lon, forecast_days=3)
        
        if not weather_data:
            error_text = (
                f"❌ Не вдалося отримати прогноз для {settlement_name} ({region})\n\n"
                f"Можливі причини:\n"
                f"• Проблеми з підключенням\n"
                f"• Тимчасовий збій сервісу\n"
                f"• Спробуйте через хвилину"
            )
            logger.error("Failed to get weather data")
            if is_callback:
                await update.callback_query.edit_message_text(error_text, parse_mode='Markdown')
            else:
                await update.message.reply_text(error_text, parse_mode='Markdown')
            return
        
        logger.info(f"Weather data received, keys: {list(weather_data.keys())}")
        
        # Отримуємо 3 повідомлення з прогнозом
        forecast_messages = weather_api.format_3day_forecast(settlement_name, region, weather_data)
        logger.info(f"Forecast messages prepared: {len(forecast_messages) if forecast_messages else 0}")
        
        if not forecast_messages:
            error_text = f"❌ Помилка обробки прогнозу для {settlement_name}"
            logger.error("No forecast messages generated")
            if is_callback:
                await update.callback_query.edit_message_text(error_text, parse_mode='Markdown')
            else:
                await update.message.reply_text(error_text, parse_mode='Markdown')
            return
        
        # ВИПРАВЛЕНО: Надсилаємо прогноз правильно
        if is_callback:
            # Для callback: редагуємо перше повідомлення, інші відправляємо новими
            logger.info("Editing first message for callback")
            await query.edit_message_text(forecast_messages[0], parse_mode='Markdown')
            
            # Відправляємо інші повідомлення
            logger.info(f"Sending {len(forecast_messages)-1} additional messages")
            for i, forecast_text in enumerate(forecast_messages[1:], 1):
                await query.message.reply_text(forecast_text, parse_mode='Markdown')
            
        else:
            # Для звичайних повідомлень
            logger.info("Processing regular message")
            if hasattr(message_to_edit, 'edit_text'):
                # Редагуємо перше повідомлення
                logger.info("Editing existing message")
                await message_to_edit.edit_text(forecast_messages[0], parse_mode='Markdown')
            else:
                # Або відправляємо нове
                logger.info("Sending new message")
                await update.message.reply_text(forecast_messages[0], parse_mode='Markdown')
            
            # Відправляємо інші повідомлення
            logger.info(f"Sending {len(forecast_messages)-1} additional messages")
            for i, forecast_text in enumerate(forecast_messages[1:], 1):
                await update.message.reply_text(forecast_text, parse_mode='Markdown')
        
        # Додаємо кнопки під останнім повідомленням
        keyboard = [
            [
                InlineKeyboardButton("🌤 Поточна погода", callback_data="current_city"),
                InlineKeyboardButton("⭐️ Додати до улюблених", callback_data="add_fav")
            ],
            [
                InlineKeyboardButton("🔍 Новий пошук", callback_data="new_search"),
                InlineKeyboardButton("↩️ Меню", callback_data="back_to_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Надсилаємо повідомлення з кнопками
        logger.info("Sending action buttons")
        if is_callback:
            await query.message.reply_text(
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
        
        logger.info(f"3-day forecast sent for {settlement_name} ({region}) via {'callback' if is_callback else 'message'}")
            
    except Exception as e:
        logger.error(f"Error processing forecast request: {e}", exc_info=True)
        error_msg = "❌ Виникла критична помилка. Спробуйте пізніше."
        
        if hasattr(update, 'callback_query'):
            try:
                await update.callback_query.edit_message_text(error_msg, parse_mode='Markdown')
            except Exception as edit_error:
                logger.error(f"Failed to edit message: {edit_error}")
                await update.callback_query.answer(error_msg)
        elif hasattr(update, 'message'):
            await update.message.reply_text(error_msg, parse_mode='Markdown')

# ============================================================================
# ОБРОБНИК ПОМИЛОК
# ============================================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник помилок"""
    logger.error(f"Bot error: {context.error}", exc_info=True)


# ============================================================================
# СПЕЦІАЛЬНІ ФУНКЦІЇ ДЛЯ ОБРОБКИ CALLBACK
# ============================================================================

async def process_current_weather_for_callback(query, context, settlement_name, region):
    """Обробка погоди для callback запитів"""
    try:
        # Зберігаємо останнє місто
        context.user_data['last_city'] = settlement_name
        context.user_data['last_region'] = region
        
        # Редагуємо повідомлення
        await query.edit_message_text(
            f"🔍 Отримую погоду для {settlement_name} ({region})...", 
            parse_mode='Markdown'
        )
        
        # Отримуємо координати
        lat, lon = settlements_db.get_coordinates(settlement_name, region)
        
        if not lat or not lon:
            await query.edit_message_text(
                f"❌ Не знайдено координат для '{settlement_name}' ({region})",
                parse_mode='Markdown'
            )
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
            await query.edit_message_text(error_text, parse_mode='Markdown')
            return
        
        # Форматуємо повідомлення
        weather_text = weather_api.format_current_weather(settlement_name, region, weather_data)
        
        if not weather_text:
            await query.edit_message_text(
                f"❌ Помилка обробки даних для {settlement_name}",
                parse_mode='Markdown'
            )
            return
        
        # Створюємо кнопки дій
        keyboard = [
            [
                InlineKeyboardButton("📅 Прогноз на 3 дні", callback_data="forecast_city"),
                InlineKeyboardButton("⭐️ Додати до улюблених", callback_data="add_fav")
            ],
            [
                InlineKeyboardButton("🔄 Оновити", callback_data="refresh"),
                InlineKeyboardButton("🔍 Новий пошук", callback_data="new_search")
            ],
            [
                InlineKeyboardButton("↩️ Меню", callback_data="back_to_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            weather_text, 
            parse_mode='Markdown', 
            reply_markup=reply_markup
        )
        
        logger.info(f"Weather sent via callback for {settlement_name} ({region})")
            
    except Exception as e:
        logger.error(f"Error processing weather request from callback: {e}")
        await query.edit_message_text(
            "❌ Виникла критична помилка. Спробуйте пізніше.",
            parse_mode='Markdown'
        )

async def process_3day_forecast_for_callback(query, context, settlement_name, region):
    """Обробка прогнозу для callback запитів"""
    try:
        # Зберігаємо останнє місто
        context.user_data['last_city'] = settlement_name
        context.user_data['last_region'] = region
        
        # Редагуємо повідомлення
        await query.edit_message_text(
            f"📅 Отримую прогноз для {settlement_name} ({region})...", 
            parse_mode='Markdown'
        )
        
        # Отримуємо координати
        lat, lon = settlements_db.get_coordinates(settlement_name, region)
        
        if not lat or not lon:
            await query.edit_message_text(
                f"❌ Не знайдено координат для '{settlement_name}' ({region})",
                parse_mode='Markdown'
            )
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
            await query.edit_message_text(error_text, parse_mode='Markdown')
            return
        
        # Отримуємо 3 повідомлення з прогнозом
        forecast_messages = weather_api.format_3day_forecast(settlement_name, region, weather_data)
        
        if not forecast_messages:
            await query.edit_message_text(
                f"❌ Помилка обробки прогнозу для {settlement_name}",
                parse_mode='Markdown'
            )
            return
        
        # Надсилаємо перше повідомлення через редагування
        await query.edit_message_text(forecast_messages[0], parse_mode='Markdown')
        
        # Надсилаємо інші повідомлення новими
        for forecast_text in forecast_messages[1:]:
            await query.message.reply_text(forecast_text, parse_mode='Markdown')
        
        # Додаємо кнопки під останнім повідомленням
        keyboard = [
            [
                InlineKeyboardButton("🌤 Поточна погода", callback_data="current_city"),
                InlineKeyboardButton("⭐️ Додати до улюблених", callback_data="add_fav")
            ],
            [
                InlineKeyboardButton("🔍 Новий пошук", callback_data="new_search"),
                InlineKeyboardButton("↩️ Меню", callback_data="back_to_menu")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Надсилаємо повідомлення з кнопками
        await query.message.reply_text(
            "👇 *Оберіть дію:*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        logger.info(f"3-day forecast sent via callback for {settlement_name} ({region})")
            
    except Exception as e:
        logger.error(f"Error processing forecast request from callback: {e}")
        await query.edit_message_text(
            "❌ Виникла критична помилка. Спробуйте пізніше.",
            parse_mode='Markdown'
        )

async def add_to_favorites_from_callback(query, context, settlement_name, region):
    """Додати місто до улюблених з callback"""
    favorites = context.user_data.get('favorites', [])
    
    # Перевіряємо, чи вже є в улюблених
    for fav in favorites:
        if fav['name'] == settlement_name and fav['region'] == region:
            await query.answer("✅ Це місто вже в улюблених!")
            return
    
    # Додаємо до улюблених
    favorites.append({
        'name': settlement_name,
        'region': region
    })
    context.user_data['favorites'] = favorites
    
    await query.answer(f"✅ {settlement_name} додано до улюблених!")

async def remove_from_favorites_from_callback(query, context, settlement_name, region):
    """Видалити місто з улюблених з callback"""
    favorites = context.user_data.get('favorites', [])
    
    # Шукаємо та видаляємо місто
    new_favorites = []
    removed = False
    for fav in favorites:
        if not (fav['name'] == settlement_name and fav['region'] == region):
            new_favorites.append(fav)
        else:
            removed = True
    
    context.user_data['favorites'] = new_favorites
    
    if removed:
        await query.answer(f"✅ {settlement_name} видалено з улюблених!")
        # Показуємо оновлений список
        await show_favorites(query, context)
    else:
        await query.answer("❌ Місто не знайдено в улюблених")

async def clear_favorites_from_callback(query, context):
    """Очистити улюблені міста з callback"""
    context.user_data['favorites'] = []
    await query.answer("✅ Улюблені міста очищено!")
    await show_favorites(query, context)

async def start_command_for_callback(query, context):
    """Команда /start для callback"""
    user = query.from_user
    
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
    
    await query.edit_message_text(
        welcome_text,
        parse_mode='Markdown'
    )
    # Відправляємо нове повідомлення з клавіатурою
    await query.message.reply_text(
        "Оберіть опцію:",
        reply_markup=get_main_keyboard()
    )

async def debug_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функція для налагодження контексту"""
    user_data = context.user_data
    logger.info(f"User data: {user_data}")
    
    if hasattr(update, 'callback_query'):
        query = update.callback_query
        await query.answer(f"Контекст: {list(user_data.keys())}")
    elif hasattr(update, 'message'):
        await update.message.reply_text(f"Контекст: {list(user_data.keys())}")




# ============================================================================
# HEALTH SERVER ДЛЯ KOYEB
# ============================================================================

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        if self.path == '/health':
            self.wfile.write(b'{"status":"healthy"}')
        else:
            self.wfile.write(b'{"status":"online"}')
    
    def log_message(self, format, *args):
        pass  # Вимкнути логування

def run_health_server():
    """Запуск health сервера"""
    port = int(os.getenv('PORT', 8000))
    print(f"🌐 Health server starting on port {port}")
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

# ============================================================================
# ОНОВЛЕНА ГОЛОВНА ФУНКЦІЯ
# ============================================================================

def main():
    """Запуск бота з health сервером"""
    try:
        print("🚀 Creating Telegram application...")
        
        # Запускаємо health сервер у окремому потоці
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        print(f"✅ Health server started on port {os.getenv('PORT', 8000)}")
        
        # Створюємо Application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Додавання обробників команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("debug", debug_context))  # Додайте цей рядок
        application.add_handler(CommandHandler("testfav", test_favorites))

        # Обробник кнопок меню
        application.add_handler(MessageHandler(
            filters.TEXT & filters.Regex(r'^(🌤|📅|🔍|🏙|⭐️|📊|❓|↩️)'), 
            handle_menu_button
        ))
        
        # Обробник інлайн-кнопок
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Обробник текстових повідомлень
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            handle_message
        ))
        
        # Обробник помилок
        application.add_error_handler(error_handler)
        
        print("✅ Application created")
        print(f"✅ Database loaded: {len(settlements_db.settlements)} settlements")
        print("🚀 Starting bot polling...")
        
        # Запускаємо бота
        application.run_polling(
            drop_pending_updates=True,
            timeout=30,
            pool_timeout=30,
            close_loop=False  # ВАЖЛИВО: не закривати loop
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()
