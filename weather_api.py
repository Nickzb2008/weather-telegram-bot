import requests
import json
import logging
from typing import Optional, Dict
from datetime import datetime
import hashlib
import time
from config import Config

logger = logging.getLogger(__name__)

class WeatherAPI:
    def __init__(self):
        self.api_key = Config.WEATHER_API_KEY
        self.cache = {}
        self.cache_duration = Config.CACHE_DURATION
        
    def get_weather(self, city: str) -> Optional[Dict]:
        """Отримати погоду для міста"""
        if not self.api_key:
            return None
            
        cache_key = hashlib.md5(city.lower().encode()).hexdigest()
        
        # Перевірка кешу
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                logger.info(f"Використано кеш для {city}")
                return cached_data
        
        try:
            # Запит до OpenWeatherMap
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'ua'
            }
            
            response = requests.get(
                Config.WEATHER_API_URL, 
                params=params, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Обробка даних
                weather_data = {
                    'city': data['name'],
                    'country': data['sys']['country'],
                    'temperature': round(data['main']['temp'], 1),
                    'feels_like': round(data['main']['feels_like'], 1),
                    'description': data['weather'][0]['description'].capitalize(),
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'wind_speed': data['wind']['speed'],
                    'wind_gust': data['wind'].get('gust', data['wind']['speed'] * 1.5),
                    'wind_deg': data['wind']['deg'],
                    'clouds': data['clouds']['all'],
                    'visibility': data.get('visibility', 10000) / 1000,  # у км
                    'timestamp': datetime.now().strftime('%H:%M')
                }
                
                # Збереження в кеш
                self.cache[cache_key] = (weather_data, time.time())
                
                return weather_data
                
            else:
                logger.error(f"API повернув помилку: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Помилка мережі: {e}")
            return None
        except KeyError as e:
            logger.error(f"Помилка обробки даних: {e}")
            return None
    
    def format_weather_message(self, data: Dict) -> str:
        """Форматування повідомлення про погоду"""
        if not data:
            return "❌ Не вдалося отримати дані про погоду."
        
        # Напрям вітру
        wind_dir = self._get_wind_direction(data['wind_deg'])
        
        # Вітер на висотах (емпіричні формули)
        wind_ground = data['wind_speed']
        wind_600 = wind_ground * 1.3
        wind_800 = wind_ground * 1.5
        wind_1000 = wind_ground * 1.8
        
        # Опади (емпіричні дані на основі хмарності)
        rain_probability = min(100, data['clouds'] * 1.5)
        
        message = f"""
🌤 *Погода в {data['city']}, {data['country']}*

🌡 Температура: *{data['temperature']}°C*
💭 Відчувається як: *{data['feels_like']}°C*
📝 {data['description']}

💧 Вологість: *{data['humidity']}%*
📊 Тиск: *{data['pressure']} гПа*
👁 Видимість: *{data['visibility']:.1f} км*
☁️ Хмарність: *{data['clouds']}%*

🌬 *Вітер на поверхні:*
• Швидкість: *{data['wind_speed']:.1f} м/с*
• Пориви: *{data['wind_gust']:.1f} м/с*
• Напрям: *{wind_dir}*

🌀 *Вітер на висотах:*
• 600м: *{wind_600:.1f} м/с, {wind_dir}*
• 800м: *{wind_800:.1f} м/с, {wind_dir}*
• 1000м: *{wind_1000:.1f} м/с, {wind_dir}*

🌧 Ймовірність опадів: *{rain_probability:.0f}%*

🕐 Оновлено: {data['timestamp']}
        """
        
        return message
    
    def _get_wind_direction(self, degrees: float) -> str:
        """Конвертувати градуси у напрям вітру"""
        directions_uk = [
            'північний', 'північно-східний', 'східний', 
            'південно-східний', 'південний', 'південно-західний',
            'західний', 'північно-західний'
        ]
        index = round(degrees / 45) % 8
        return directions_uk[index]
    
    def cleanup_cache(self):
        """Очищення старого кешу"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.cache_duration
        ]
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Очищено {len(expired_keys)} записів з кешу")