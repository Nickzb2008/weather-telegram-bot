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
                    'wind_speed_10m', 'wind_direction_10m'
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
            logger.info(f"📋 Request params: {params}")
            
            response = requests.get(self.base_url, params=params, timeout=15)
            logger.info(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Weather data received")
                logger.info(f"📊 Data keys: {list(data.keys())}")
                
                if 'daily' in data:
                    logger.info(f"📅 Daily keys: {list(data['daily'].keys())}")
                    if 'time' in data['daily']:
                        logger.info(f"📆 Daily time entries: {len(data['daily']['time'])}")
                
                return data
            else:
                logger.error(f"❌ Open-Meteo API error: {response.status_code}")
                logger.error(f"❌ Response text: {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Open-Meteo error: {e}", exc_info=True)
            return None

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
    
    def calculate_cloud_base(self, temperature: float, humidity: float) -> Optional[int]:
        """Розрахувати нижню кромку хмар"""
        if temperature is None or humidity is None:
            return None
        
        t = temperature
        rh = humidity
        
        # Формула Магнуса для точки роси
        a = 17.27
        b = 237.7
        alpha = ((a * t) / (b + t)) + math.log(rh / 100.0)
        dew_point = (b * alpha) / (a - alpha)
        
        # Формула для висоти хмар (метри)
        cloud_base = 125 * (t - dew_point)
        
        # Обмеження
        if cloud_base < 100:
            return 100
        elif cloud_base > 5000:
            return 5000
        return int(cloud_base)
    
    def format_current_weather(self, settlement_name: str, region: str, weather_data: dict) -> str:
        """Форматувати повідомлення про поточну погоду"""
        try:
            current = weather_data.get('current', {})
            
            # Основні дані
            temp = current.get('temperature_2m', 0)
            feels_like = current.get('apparent_temperature', temp)
            humidity = current.get('relative_humidity_2m', 0)
            pressure = current.get('pressure_msl', 0)
            cloud_cover = current.get('cloud_cover', 0)
            weather_code = current.get('weather_code', 0)
            visibility = current.get('visibility', 10000) / 1000  # у км
            
            # Опади
            precipitation = current.get('precipitation', 0)
            rain = current.get('rain', 0)
            snowfall = current.get('snowfall', 0)
            
            # Вітер
            wind_speed_10m = current.get('wind_speed_10m', 0)
            wind_dir_10m = current.get('wind_direction_10m')
            wind_gusts_10m = current.get('wind_gusts_10m', 0)
            
            # Опис погоди
            weather_desc = self.get_weather_description(weather_code)
            
            # Нижня кромка хмар
            cloud_base = self.calculate_cloud_base(temp, humidity)
            
            # Формуємо повідомлення
            message = f"🌤 *Погода в {settlement_name} ({region})*\n\n"
            
            message += f"📊 *Загальна інформація:*\n"
            message += f"• Стан: {weather_desc}\n"
            message += f"• Температура: *{temp:.1f}°C*\n"
            message += f"• Відчувається як: *{feels_like:.1f}°C*\n"
            message += f"• Вологість: *{humidity}%*\n"
            message += f"• Тиск: *{pressure:.0f} hPa*\n"
            message += f"• Видимість: *{visibility:.1f} км*\n\n"
            
            # Вітер на землі
            wind_dir_text = self.get_wind_direction(wind_dir_10m)
            message += f"💨 *Вітер:*\n"
            message += f"• Швидкість: *{wind_speed_10m:.1f} м/с*\n"
            message += f"• Пориви: *{wind_gusts_10m:.1f} м/с*\n"
            message += f"• Напрямок: *{wind_dir_text}*\n\n"
            
            # Опади
            message += f"🌧 *Опади (за годину):*\n"
            message += f"• Загальні: *{precipitation:.1f} мм*\n"
            if rain > 0:
                message += f"• Дощ: *{rain:.1f} мм*\n"
            if snowfall > 0:
                message += f"• Сніг: *{snowfall:.1f} мм*\n"
            
            # Хмарність
            if cloud_base:
                message += f"\n☁️ *Хмарність:* {cloud_cover}%, нижня кромка: *{cloud_base} м*"
            else:
                message += f"\n☁️ *Хмарність:* {cloud_cover}%"
            
            message += f"\n\n📡 *Джерело:* Open-Meteo API"
            message += f"\n🔄 *Оновлено:* {datetime.now().strftime('%H:%M %d.%m.%Y')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting current weather: {e}")
            return None
    
    def format_3day_forecast(self, settlement_name: str, region: str, weather_data: dict) -> List[str]:
        """Форматувати прогноз на 3 дні (3 окремих повідомлення)"""
        logger.info(f"🔧 Formatting 3-day forecast for {settlement_name} ({region})")
        
        try:
            daily = weather_data.get('daily', {})
            logger.info(f"📊 Daily data keys: {list(daily.keys())}")
            
            if 'time' not in daily:
                logger.error("❌ 'time' key not found in daily data")
                return []
            
            if len(daily['time']) == 0:
                logger.error("❌ 'time' array is empty")
                return []
            
            logger.info(f"📅 Days available: {len(daily['time'])}")
            
            messages = []
            
            for i in range(min(3, len(daily['time']))):
                date_str = daily['time'][i]
                logger.info(f"📅 Processing day {i+1}: {date_str}")
                
                try:
                    # Конвертуємо дату
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_formatted = date_obj.strftime('%d.%m.%Y')
                    day_name = self._get_day_name(date_obj)
                    logger.info(f"📆 Formatted date: {date_formatted} ({day_name})")
                except Exception as e:
                    logger.error(f"❌ Error parsing date {date_str}: {e}")
                    date_formatted = date_str
                    day_name = ""
                
                # Отримуємо дані для дня
                max_temp = daily.get('temperature_2m_max', [0])[i] if i < len(daily.get('temperature_2m_max', [])) else 0
                min_temp = daily.get('temperature_2m_min', [0])[i] if i < len(daily.get('temperature_2m_min', [])) else 0
                precip_sum = daily.get('precipitation_sum', [0])[i] if i < len(daily.get('precipitation_sum', [])) else 0
                precip_hours = daily.get('precipitation_hours', [0])[i] if i < len(daily.get('precipitation_hours', [])) else 0
                weather_code = daily.get('weather_code', [0])[i] if i < len(daily.get('weather_code', [])) else 0
                sunrise = daily.get('sunrise', [''])[i] if i < len(daily.get('sunrise', [])) else ''
                sunset = daily.get('sunset', [''])[i] if i < len(daily.get('sunset', [])) else ''
                wind_speed_max = daily.get('wind_speed_10m_max', [0])[i] if i < len(daily.get('wind_speed_10m_max', [])) else 0
                wind_gusts_max = daily.get('wind_gusts_10m_max', [0])[i] if i < len(daily.get('wind_gusts_10m_max', [])) else 0
                wind_dir = daily.get('wind_direction_10m_dominant', [0])[i] if i < len(daily.get('wind_direction_10m_dominant', [])) else 0
                
                logger.info(f"🌡 Day {i+1} data: max_temp={max_temp}, min_temp={min_temp}, precip={precip_sum}")
                
                # Опис погоди
                weather_desc = self.get_weather_description(weather_code)
                weather_emoji = self.get_weather_emoji(weather_code)
                
                # Форматуємо час сходу/заходу сонця
                sunrise_time = ""
                sunset_time = ""
                if sunrise:
                    try:
                        sunrise_time = datetime.fromisoformat(sunrise.replace('Z', '+00:00')).strftime('%H:%M')
                        logger.info(f"🌅 Sunrise: {sunrise_time}")
                    except Exception as e:
                        logger.error(f"❌ Error parsing sunrise {sunrise}: {e}")
                        sunrise_time = sunrise
                if sunset:
                    try:
                        sunset_time = datetime.fromisoformat(sunset.replace('Z', '+00:00')).strftime('%H:%M')
                        logger.info(f"🌇 Sunset: {sunset_time}")
                    except Exception as e:
                        logger.error(f"❌ Error parsing sunset {sunset}: {e}")
                        sunset_time = sunset
                
                # Напрям вітру
                wind_dir_text = self.get_wind_direction(wind_dir)
                
                # Формуємо повідомлення для дня
                if i == 0:
                    title = f"📅 *Прогноз на сьогодні ({date_formatted})*"
                elif i == 1:
                    title = f"📅 *Прогноз на завтра ({date_formatted})*"
                else:
                    title = f"📅 *Прогноз на {day_name} ({date_formatted})*"
                
                message = f"{title}\n"
                message += f"📍 *{settlement_name} ({region})*\n\n"
                
                message += f"🌤 *Загальна інформація:*\n"
                message += f"• Стан: {weather_emoji} {weather_desc}\n"
                message += f"• Температура: *{min_temp:.0f}° - {max_temp:.0f}°C*\n"
                
                if precip_sum > 0:
                    message += f"• Опади: *{precip_sum:.1f} мм* ({precip_hours:.0f} год)\n"
                else:
                    message += f"• Опади: немає\n"
                
                message += f"• Вітер: *{wind_speed_max:.1f} м/с* (пориви до {wind_gusts_max:.1f} м/с)\n"
                message += f"• Напрям вітру: {wind_dir_text}\n"
                
                if sunrise_time and sunset_time:
                    message += f"• Сонце: {sunrise_time} - {sunset_time}\n"
                
                # Додаємо почасовий прогноз для сьогодні
                if i == 0:
                    hourly_section = self._format_hourly_forecast(weather_data)
                    if hourly_section:
                        message += hourly_section
                
                message += f"\n📡 *Джерело:* Open-Meteo API"
                
                messages.append(message)
                logger.info(f"✅ Day {i+1} message created: {len(message)} chars")
            
            logger.info(f"✅ Generated {len(messages)} forecast messages total")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error formatting 3-day forecast: {e}", exc_info=True)
            return []

    def _format_hourly_forecast(self, weather_data: dict) -> str:
        """Форматувати почасовий прогноз"""
        logger.info("🔧 Formatting hourly forecast")
        
        try:
            hourly = weather_data.get('hourly', {})
            logger.info(f"⏰ Hourly data keys: {list(hourly.keys())}")
            
            if 'time' not in hourly or len(hourly['time']) == 0:
                logger.warning("❌ No hourly time data available")
                return ""
            
            # Знаходимо поточну годину
            current_hour = datetime.now().hour
            logger.info(f"🕐 Current hour: {current_hour}")
            
            # Знаходимо наступні 6 годин
            forecast_hours = []
            for i, time_str in enumerate(hourly['time'][:24]):  # Перевіряємо тільки наступні 24 години
                try:
                    hour = int(time_str.split('T')[1].split(':')[0])
                    if hour >= current_hour and len(forecast_hours) < 6:
                        forecast_hours.append({
                            'hour': hour,
                            'temp': hourly.get('temperature_2m', [0])[i] if i < len(hourly.get('temperature_2m', [])) else 0,
                            'precip_prob': hourly.get('precipitation_probability', [0])[i] if i < len(hourly.get('precipitation_probability', [])) else 0,
                            'weather_code': hourly.get('weather_code', [0])[i] if i < len(hourly.get('weather_code', [])) else 0,
                            'wind_speed': hourly.get('wind_speed_10m', [0])[i] if i < len(hourly.get('wind_speed_10m', [])) else 0
                        })
                        logger.info(f"⏱ Added hour {hour}: temp={forecast_hours[-1]['temp']}")
                except Exception as e:
                    logger.error(f"❌ Error parsing hour from {time_str}: {e}")
                    continue
            
            logger.info(f"✅ Found {len(forecast_hours)} forecast hours")
            
            if not forecast_hours:
                return ""
            
            message = "\n⏰ *Почасовий прогноз:*\n"
            
            for forecast in forecast_hours:
                emoji = self.get_weather_emoji(forecast['weather_code'])
                message += f"• {forecast['hour']:02d}:00 - {emoji} {forecast['temp']:.0f}°C"
                if forecast['precip_prob'] > 0:
                    message += f", {forecast['precip_prob']}% опади"
                message += f", вітер {forecast['wind_speed']:.1f} м/с\n"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error formatting hourly forecast: {e}")
            return ""

    def _get_day_name(self, date_obj: datetime) -> str:
        """Отримати назву дня тижня українською"""
        days = {
            0: "понеділок",
            1: "вівторок",
            2: "середа",
            3: "четвер",
            4: "п'ятниця",
            5: "субота",
            6: "неділя"
        }
        return days.get(date_obj.weekday(), "")

# Глобальний екземпляр API погоди
weather_api = WeatherAPI()