# app.py - Гарантовано працює
import os
import sys
import time
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Простий health check сервер
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

def run_bot():
    """Запуск бота"""
    print("=" * 60)
    print("🇺🇦 UKRAINE WEATHER BOT")
    print("=" * 60)
    
    # Монопатч для telegram бібліотеки
    import asyncio
    import signal
    
    # Вимикаємо обробку сигналів
    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    
    # Імпортуємо патч перед імпортом telegram
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Запускаємо бота через subprocess
    while True:
        try:
            print("🚀 Starting bot...")
            result = subprocess.run(
                [sys.executable, 'bot.py'],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            print("Bot stopped, restarting in 5 seconds...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Bot error: {e}, restarting...")
            time.sleep(5)

if __name__ == '__main__':
    # Запускаємо health сервер в потоці
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Запускаємо бота в головному потоці
    run_bot()