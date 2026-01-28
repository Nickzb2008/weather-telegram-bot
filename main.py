# main.py - Спрощена версія для Koyeb (ВИПРАВЛЕНО)
import os
import sys
import signal
import asyncio
import logging

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("🇺🇦 UKRAINE WEATHER BOT - KOYEB OPTIMIZED")
print("=" * 60)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found!")
    sys.exit(1)

print(f"✅ TELEGRAM_TOKEN: OK")

# Вимикаємо обробку сигналів для уникнення помилок
signal.signal(signal.SIGINT, signal.SIG_IGN)
signal.signal(signal.SIGTERM, signal.SIG_IGN)

async def main():
    """Головна асинхронна функція"""
    try:
        # Імпорт бібліотек telegram
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
        
        # Імпорт внутрішніх модулів тут, щоб уникнути конфліктів
        from bot import start_command, help_command, handle_message, handle_menu_button
        from bot import button_handler, error_handler
        from bot import settlements_db
        
        # Створюємо Application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Додавання обробників команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        
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
        
        # Запускаємо polling з вимкненими сигналами
        await application.run_polling(
            drop_pending_updates=True,
            timeout=30,
            pool_timeout=30,
            allowed_updates=None,
            close_loop=False
        )
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == '__main__':
    # Створюємо новий event loop без обробки сигналів
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Запускаємо асинхронну функцію
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)
    finally:
        loop.close()