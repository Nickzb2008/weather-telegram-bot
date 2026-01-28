import requests
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class WeatherAPI:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_weather(self, lat: float, lon: float, forecast_days: int = 3) -> Optional[dict]:
        """Отримати погоду з Open-Meteo API"""
        logger.info(f"🌤 Getting weather for lat={lat}, lon={lon}, days={forecast_days}")
        
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': [
                    'temperature_2m', 'relative_humidity_2m', 'apparent_temperature',
                    'precipitation', 'rain', 'snowfall', 'weather_code',
                    'cloud_cover', 'pressure_msl', 'wind_speed_10m',
                    'wind_direction_10m', 'wind_gusts_10m', 'visibility'
                ],
                'hourly': [
                    'temperature_2m', 'relative_humidity_2m', 'precipitation_probability',
                    'precipitation', 'rain', 'snowfall', 'weather_code',
                    'wind_speed_10m', 'wind_direction_10m',
                    # Додаємо вітер на різних висотах
                    'wind_speed_80m', 'wind_direction_80m',
                    'wind_speed_120m', 'wind_direction_120m',
                    'wind_speed_180m', 'wind_direction_180m'
                ],
                'daily': [
                    'temperature_2m_max', 'temperature_2m_min',
                    'precipitation_sum', 'precipitation_hours',
                    'weather_code', 'sunrise', 'sunset',
                    'wind_speed_10m_max', 'wind_gusts_10m_max',
                    'wind_direction_10m_dominant'
                ],
                'timezone': 'auto',
                'forecast_days': forecast_days
            }
            
            logger.info(f"🌍 Request URL: {self.base_url}")
            
            response = requests.get(self.base_url, params=params, timeout=15)
            logger.info(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Weather data received")
                return data
            else:
                logger.error(f"❌ Open-Meteo API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Open-Meteo error: {e}", exc_info=True)
            return None

    # ... інші функції залишаються незмінними до _format_hourly_forecast ...

    def _format_hourly_forecast(self, weather_data: dict) -> str:
        """Форматувати почасовий прогноз з даними про вітер на висотах"""
        logger.info("🔧 Formatting hourly forecast with altitude winds")
        
        try:
            hourly = weather_data.get('hourly', {})
            
            if 'time' not in hourly or len(hourly['time']) == 0:
                logger.warning("❌ No hourly time data available")
                return ""
            
            # Знаходимо поточну годину
            current_hour = datetime.now().hour
            logger.info(f"🕐 Current hour: {current_hour}")
            
            # Знаходимо наступні 6 годин
            forecast_hours = []
            for i, time_str in enumerate(hourly['time'][:24]):
                try:
                    hour = int(time_str.split('T')[1].split(':')[0])
                    if hour >= current_hour and len(forecast_hours) < 6:
                        forecast_hours.append({
                            'hour': hour,
                            'temp': hourly.get('temperature_2m', [0])[i] if i < len(hourly.get('temperature_2m', [])) else 0,
                            'precip_prob': hourly.get('precipitation_probability', [0])[i] if i < len(hourly.get('precipitation_probability', [])) else 0,
                            'precipitation': hourly.get('precipitation', [0])[i] if i < len(hourly.get('precipitation', [])) else 0,
                            'weather_code': hourly.get('weather_code', [0])[i] if i < len(hourly.get('weather_code', [])) else 0,
                            'wind_speed': hourly.get('wind_speed_10m', [0])[i] if i < len(hourly.get('wind_speed_10m', [])) else 0,
                            'wind_dir_10m': hourly.get('wind_direction_10m', [0])[i] if i < len(hourly.get('wind_direction_10m', [])) else 0,
                            # Додаємо дані про вітер на висотах
                            'wind_speed_80m': hourly.get('wind_speed_80m', [0])[i] if i < len(hourly.get('wind_speed_80m', [])) else 0,
                            'wind_dir_80m': hourly.get('wind_direction_80m', [0])[i] if i < len(hourly.get('wind_direction_80m', [])) else 0,
                            'wind_speed_120m': hourly.get('wind_speed_120m', [0])[i] if i < len(hourly.get('wind_speed_120m', [])) else 0,
                            'wind_dir_120m': hourly.get('wind_direction_120m', [0])[i] if i < len(hourly.get('wind_direction_120m', [])) else 0,
                            'wind_speed_180m': hourly.get('wind_speed_180m', [0])[i] if i < len(hourly.get('wind_speed_180m', [])) else 0,
                            'wind_dir_180m': hourly.get('wind_direction_180m', [0])[i] if i < len(hourly.get('wind_direction_180m', [])) else 0,
                        })
                except Exception as e:
                    logger.error(f"❌ Error parsing hour from {time_str}: {e}")
                    continue
            
            if not forecast_hours:
                return ""
            
            # Форматуємо почасовий прогноз
            message = "\n⏰ *Почасовий прогноз:*\n"
            
            for forecast in forecast_hours:
                emoji = self.get_weather_emoji(forecast['weather_code'])
                
                # Форматуємо інформацію про опади
                precip_info = ""
                if forecast['precip_prob'] > 0:
                    precip_info = f", {forecast['precip_prob']}% опади"
                if forecast['precipitation'] > 0:
                    precip_info += f" ({forecast['precipitation']:.1f} мм)"
                
                message += f"• {forecast['hour']:02d}:00 - {emoji} {forecast['temp']:.0f}°C"
                message += f"{precip_info}"
                message += f", вітер {forecast['wind_speed']:.1f} м/с\n"
            
            # Додаємо вітер на висотах (беремо дані з першого прогнозу)
            if forecast_hours:
                first_forecast = forecast_hours[0]
                
                # Перевіряємо наявність даних про вітер на висотах
                has_altitude_wind = any([
                    first_forecast.get('wind_dir_80m'),
                    first_forecast.get('wind_dir_120m'),
                    first_forecast.get('wind_dir_180m')
                ])
                
                if has_altitude_wind:
                    message += "\n💨 *Вітер на висотах:*\n"
                    
                    # Вітер на ~400м (80м вежа + висота)
                    if first_forecast.get('wind_dir_80m'):
                        wind_400_dir = self.get_wind_direction(first_forecast['wind_dir_80m'])
                        message += f"• ~400м: {wind_400_dir}\n"
                    
                    # Вітер на ~600м (120м вежа + висота)
                    if first_forecast.get('wind_dir_120m'):
                        wind_600_dir = self.get_wind_direction(first_forecast['wind_dir_120m'])
                        message += f"• ~600м: {wind_600_dir}\n"
                    
                    # Вітер на ~800м (180м вежа + висота)
                    if first_forecast.get('wind_dir_180m'):
                        wind_800_dir = self.get_wind_direction(first_forecast['wind_dir_180m'])
                        message += f"• ~800м: {wind_800_dir}\n"
                    
                    # Якщо немає даних для 1000м, використовуємо найвищі доступні
                    # або екстраполюємо
                    wind_1000_dir = "Немає даних"
                    if first_forecast.get('wind_dir_180m'):
                        # Проста екстраполяція
                        wind_1000_dir = self.get_wind_direction(first_forecast['wind_dir_180m'])
                        message += f"• ~1000м: {wind_1000_dir}\n"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error formatting hourly forecast: {e}", exc_info=True)
            return ""

    # Альтернативна версія з використанням інших висот (якщо Open-Meteo підтримує)
    def _format_hourly_forecast_alternative(self, weather_data: dict) -> str:
        """Альтернативна версія форматування почасового прогнозу"""
        logger.info("🔧 Formatting hourly forecast (alternative)")
        
        try:
            hourly = weather_data.get('hourly', {})
            
            if 'time' not in hourly or len(hourly['time']) == 0:
                return ""
            
            current_hour = datetime.now().hour
            forecast_hours = []
            
            for i, time_str in enumerate(hourly['time'][:24]):
                try:
                    hour = int(time_str.split('T')[1].split(':')[0])
                    if hour >= current_hour and len(forecast_hours) < 6:
                        forecast_hours.append({
                            'hour': hour,
                            'temp': hourly.get('temperature_2m', [0])[i] if i < len(hourly.get('temperature_2m', [])) else 0,
                            'precip_prob': hourly.get('precipitation_probability', [0])[i] if i < len(hourly.get('precipitation_probability', [])) else 0,
                            'precipitation': hourly.get('precipitation', [0])[i] if i < len(hourly.get('precipitation', [])) else 0,
                            'weather_code': hourly.get('weather_code', [0])[i] if i < len(hourly.get('weather_code', [])) else 0,
                            'wind_speed': hourly.get('wind_speed_10m', [0])[i] if i < len(hourly.get('wind_speed_10m', [])) else 0,
                            'wind_dir_10m': hourly.get('wind_direction_10m', [0])[i] if i < len(hourly.get('wind_direction_10m', [])) else 0,
                        })
                except:
                    continue
            
            if not forecast_hours:
                return ""
            
            message = "\n⏰ *Почасовий прогноз:*\n"
            
            for forecast in forecast_hours:
                emoji = self.get_weather_emoji(forecast['weather_code'])
                
                precip_info = ""
                if forecast['precip_prob'] > 0:
                    precip_info = f", {forecast['precip_prob']}% опади"
                if forecast['precipitation'] > 0:
                    precip_info += f" ({forecast['precipitation']:.1f} мм)"
                
                message += f"• {forecast['hour']:02d}:00 - {emoji} {forecast['temp']:.0f}°C"
                message += f"{precip_info}"
                message += f", вітер {forecast['wind_speed']:.1f} м/с\n"
            
            # Якщо немає даних про вітер на висотах, використовуємо земний вітер
            # або пропонуємо заміну
            message += "\n💨 *Вітер на висотах:*\n"
            message += "• ~400м: дані відсутні (використано земний вітер)\n"
            message += "• ~600м: дані відсутні (використано земний вітер)\n"
            message += "• ~800м: дані відсутні (використано земний вітер)\n"
            message += "• ~1000м: дані відсутні (використано земний вітер)\n"
            message += "\nℹ️ *Примітка:* Вітер на висотах може відрізнятись від земного.\n"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error in alternative forecast formatting: {e}")
            return ""

    # Інші функції залишаються незмінними
    def get_wind_direction(self, degrees: float) -> str:
        """Конвертувати градуси у назву напрямку вітру"""
        if degrees is None:
            return "Не визначено"
        
        directions = ["Північний", "Північно-східний", "Східний", "Південно-східний",
                     "Південний", "Південно-західний", "Західний", "Північно-західний"]
        index = round(degrees / 45) % 8
        return f"{directions[index]} ({int(degrees)}°)"
    
    def get_weather_description(self, weather_code: int) -> str:
        """Отримати опис погоди за кодом Open-Meteo"""
        weather_codes = {
            0: "☀️ Ясне небо", 1: "🌤 Переважно ясно", 2: "⛅️ Мінлива хмарність", 3: "☁️ Хмарно",
            45: "🌫 Туман", 48: "🌫 Покритий інеєм туман",
            51: "🌦 Легка мряка", 53: "🌦 Помірна мряка", 55: "🌧 Густа мряка",
            56: "🌨 Легка мряка, що замерзає", 57: "🌨 Густа мряка, що замерзає",
            61: "🌧 Невеликий дощ", 63: "🌧 Помірний дощ", 65: "🌧 Сильний дощ",
            66: "🌧 Дощ, що замерзає", 67: "🌧 Сильний дощ, що замерзає",
            71: "🌨 Невеликий снігопад", 73: "🌨 Помірний снігопад", 75: "🌨 Сильний снігопад",
            77: "🌨 Сніжинки", 80: "⛈ Невеликі зливи", 81: "⛈ Помірні зливи", 82: "⛈ Сильні зливи",
            85: "❄️ Невеликі снігові зливи", 86: "❄️ Сильні снігові зливи",
            95: "⛈ Гроза", 96: "⛈ Гроза з градом", 99: "⛈ Сильна гроза з градом"
        }
        return weather_codes.get(weather_code, "❓ Невідомо")
    
    def get_weather_emoji(self, weather_code: int) -> str:
        """Отримати емодзі для погоди"""
        emoji_codes = {
            0: "☀️", 1: "🌤", 2: "⛅️", 3: "☁️",
            45: "🌫", 48: "🌫",
            51: "🌦", 53: "🌦", 55: "🌧",
            56: "🌨", 57: "🌨",
            61: "🌧", 63: "🌧", 65: "🌧",
            66: "🌧", 67: "🌧",
            71: "🌨", 73: "🌨", 75: "🌨",
            77: "🌨", 80: "⛈", 81: "⛈", 82: "⛈",
            85: "❄️", 86: "❄️",
            95: "⛈", 96: "⛈", 99: "⛈"
        }
        return emoji_codes.get(weather_code, "❓")

# Глобальний екземпляр API погоди
weather_api = WeatherAPI()