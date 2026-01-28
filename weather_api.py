import requests
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class WeatherAPI:
    def __init__(self):
        self.open_meteo_url = "https://api.open-meteo.com/v1/forecast"
        
        # Використовуємо Open-Meteo для висотного вітру (безкоштовно)
        # Open-Meteo надає вітер на 10м, 80м, 100м, 120м, 180м у безкоштовному тарифі
        
        # Відповідність рівнів до висоти:
        self.wind_levels = {
            '10m': 10,
            '80m': 80,    # ~400-500м фактично
            '100m': 100,  # ~600-700м фактично
            '120m': 120,  # ~700-800м фактично
            '180m': 180   # ~800-1000м фактично
        }
    
    def get_weather(self, lat: float, lon: float, forecast_days: int = 3) -> Optional[dict]:
        """Отримати погоду з Open-Meteo API з даними про вітер на висотах"""
        logger.info(f"🌤 Getting weather for lat={lat}, lon={lon}, days={forecast_days}")
        
        try:
            # Запит з даними про вітер на різних висотах
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': [
                    'temperature_2m', 'relative_humidity_2m', 'apparent_temperature',
                    'precipitation', 'weather_code', 'pressure_msl', 
                    'wind_speed_10m', 'wind_direction_10m', 'wind_gusts_10m'
                ],
                'hourly': [
                    'temperature_2m', 'precipitation_probability',
                    'precipitation', 'weather_code',
                    # Вітер на різних висотах
                    'wind_speed_10m', 'wind_direction_10m',
                    'wind_speed_80m', 'wind_direction_80m',
                    'wind_speed_100m', 'wind_direction_100m',
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
            
            logger.info(f"🌍 Open-Meteo URL: {self.open_meteo_url}")
            
            response = requests.get(self.open_meteo_url, params=params, timeout=15)
            logger.info(f"📡 Open-Meteo response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Open-Meteo data received")
                
                # Додаємо оброблені дані про вітер на висотах
                altitude_wind_data = self._extract_altitude_wind_data(data)
                if altitude_wind_data:
                    data['altitude_wind'] = altitude_wind_data
                    logger.info(f"✅ Extracted wind data for {len(altitude_wind_data)} altitudes")
                
                return data
            else:
                # Спрощений запит, якщо перший не працює
                logger.error(f"❌ Detailed request failed, trying simplified")
                return self._get_simplified_weather(lat, lon, forecast_days)
                
        except Exception as e:
            logger.error(f"❌ Open-Meteo error: {e}")
            return self._get_simplified_weather(lat, lon, forecast_days)
    
    def _get_simplified_weather(self, lat: float, lon: float, forecast_days: int = 3) -> Optional[dict]:
        """Спрощений запит без даних про висотний вітер"""
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': [
                    'temperature_2m', 'relative_humidity_2m', 'apparent_temperature',
                    'precipitation', 'weather_code', 'pressure_msl', 
                    'wind_speed_10m', 'wind_direction_10m', 'wind_gusts_10m'
                ],
                'hourly': [
                    'temperature_2m', 'precipitation_probability',
                    'precipitation', 'weather_code',
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
            
            response = requests.get(self.open_meteo_url, params=params, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Simplified weather data received")
                return response.json()
            else:
                logger.error(f"❌ Simplified request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Simplified request error: {e}")
            return None
    
    def _extract_altitude_wind_data(self, weather_data: dict) -> List[Dict]:
        """Витягти дані про вітер на різних висотах з Open-Meteo"""
        try:
            hourly = weather_data.get('hourly', {})
            if not hourly:
                return []
            
            # Беремо дані для поточної години
            current_hour = datetime.now().hour
            hour_index = min(current_hour, len(hourly.get('time', [])) - 1) if hourly.get('time') else 0
            
            wind_data = []
            
            # Перевіряємо доступність даних для кожної висоти
            altitude_mapping = [
                ('80m', 400, 'wind_speed_80m', 'wind_direction_80m'),
                ('100m', 600, 'wind_speed_100m', 'wind_direction_100m'),
                ('120m', 800, 'wind_speed_120m', 'wind_direction_120m'),
                ('180m', 1000, 'wind_speed_180m', 'wind_direction_180m'),
            ]
            
            for level_name, altitude, speed_key, dir_key in altitude_mapping:
                if (speed_key in hourly and dir_key in hourly and 
                    len(hourly[speed_key]) > hour_index and len(hourly[dir_key]) > hour_index):
                    
                    wind_speed = hourly[speed_key][hour_index]
                    wind_direction = hourly[dir_key][hour_index]
                    
                    if wind_speed is not None and wind_direction is not None:
                        wind_data.append({
                            'altitude': altitude,
                            'level': level_name,
                            'speed': wind_speed,
                            'direction': wind_direction,
                            'direction_text': self.get_wind_direction(wind_direction)
                        })
                        logger.info(f"✅ Wind at {altitude}m: {wind_speed:.1f} m/s, {wind_direction:.0f}°")
                    else:
                        logger.warning(f"⚠️ No data for {altitude}m ({level_name})")
                else:
                    logger.warning(f"⚠️ Keys missing for {altitude}m: {speed_key}, {dir_key}")
            
            return wind_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting altitude wind data: {e}")
            return []
    
    def get_wind_direction(self, degrees: float) -> str:
        """Конвертувати градуси у назву напрямку вітру"""
        if degrees is None:
            return "Не визначено"
        
        directions = [
            "Північний", "Північно-східний", "Східний", "Південно-східний",
            "Південний", "Південно-західний", "Західний", "Північно-західний"
        ]
        index = round(degrees / 45) % 8
        return directions[index]
    
    def get_weather_description(self, weather_code: int) -> str:
        """Отримати опис погоди за кодом Open-Meteo"""
        weather_codes = {
            0: "☀️ Ясне небо", 
            1: "🌤 Переважно ясно", 
            2: "⛅️ Мінлива хмарність", 
            3: "☁️ Хмарно",
            45: "🌫 Туман", 
            48: "🌫 Покритий інеєм туман",
            51: "🌦 Легка мряка", 
            53: "🌦 Помірна мряка", 
            55: "🌧 Густа мряка",
            56: "🌨 Легка мряка, що замерзає", 
            57: "🌨 Густа мряка, що замерзає",
            61: "🌧 Невеликий дощ", 
            63: "🌧 Помірний дощ", 
            65: "🌧 Сильний дощ",
            66: "🌧 Дощ, що замерзає", 
            67: "🌧 Сильний дощ, що замерзає",
            71: "🌨 Невеликий снігопад", 
            73: "🌨 Помірний снігопад", 
            75: "🌨 Сильний снігопад",
            77: "🌨 Сніжинки", 
            80: "⛈ Невеликі зливи", 
            81: "⛈ Помірні зливи", 
            82: "⛈ Сильні зливи",
            85: "❄️ Невеликі снігові зливи", 
            86: "❄️ Сильні снігові зливи",
            95: "⛈ Гроза", 
            96: "⛈ Гроза з градом", 
            99: "⛈ Сильна гроза з градом"
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
    
    def format_current_weather(self, settlement_name: str, region: str, weather_data: dict) -> str:
        """Форматувати повідомлення про поточну погоду"""
        try:
            current = weather_data.get('current', {})
            
            # Основні дані
            temp = current.get('temperature_2m', 0)
            feels_like = current.get('apparent_temperature', temp)
            humidity = current.get('relative_humidity_2m', 0)
            pressure = current.get('pressure_msl', 0)
            weather_code = current.get('weather_code', 0)
            
            # Опади
            precipitation = current.get('precipitation', 0)
            
            # Вітер на землі
            wind_speed_10m = current.get('wind_speed_10m', 0)
            wind_dir_10m = current.get('wind_direction_10m')
            wind_gusts_10m = current.get('wind_gusts_10m', 0)
            
            # Опис погоди
            weather_desc = self.get_weather_description(weather_code)
            weather_emoji = self.get_weather_emoji(weather_code)
            
            # Формуємо повідомлення
            message = f"🌤 *Погода в {settlement_name} ({region})*\n\n"
            
            message += f"📊 *Загальна інформація:*\n"
            message += f"• Стан: {weather_emoji} {weather_desc}\n"
            message += f"• Температура: *{temp:.1f}°C*\n"
            message += f"• Відчувається як: *{feels_like:.1f}°C*\n"
            
            if precipitation > 0:
                message += f"• Опади: *{precipitation:.1f} мм*\n"
            
            message += f"• Вітер: *{wind_speed_10m:.1f} м/с* (пориви до {wind_gusts_10m:.1f} м/с)\n"
            
            if wind_dir_10m:
                wind_dir_text = self.get_wind_direction(wind_dir_10m)
                message += f"• Напрям вітру: {wind_dir_text} ({int(wind_dir_10m)}°)\n"
            
            message += f"• Вологість: *{humidity}%*\n"
            message += f"• Тиск: *{pressure:.0f} hPa*\n"
            
            # Додаємо почасовий прогноз
            hourly_section = self._format_hourly_forecast(weather_data)
            if hourly_section:
                message += hourly_section
            
            # Додаємо вітер на висотах
            altitude_section = self._format_altitude_wind(weather_data.get('altitude_wind', []))
            if altitude_section:
                message += altitude_section
            
            message += f"\n📡 *Джерело:* Open-Meteo API"
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
            
            if 'time' not in daily:
                logger.error("❌ 'time' key not found in daily data")
                return []
            
            if len(daily['time']) == 0:
                logger.error("❌ 'time' array is empty")
                return []
            
            messages = []
            
            for i in range(min(3, len(daily['time']))):
                date_str = daily['time'][i]
                
                try:
                    # Конвертуємо дату
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_formatted = date_obj.strftime('%d.%m.%Y')
                    day_name = self._get_day_name(date_obj)
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
                
                # Опис погоди
                weather_desc = self.get_weather_description(weather_code)
                weather_emoji = self.get_weather_emoji(weather_code)
                
                # Форматуємо час сходу/заходу сонця
                sunrise_time = ""
                sunset_time = ""
                if sunrise:
                    try:
                        sunrise_time = datetime.fromisoformat(sunrise.replace('Z', '+00:00')).strftime('%H:%M')
                    except Exception as e:
                        sunrise_time = sunrise
                if sunset:
                    try:
                        sunset_time = datetime.fromisoformat(sunset.replace('Z', '+00:00')).strftime('%H:%M')
                    except Exception as e:
                        sunset_time = sunset
                
                # Напрям вітру
                wind_dir_text = ""
                if wind_dir:
                    wind_dir_text = f"{self.get_wind_direction(wind_dir)} ({int(wind_dir)}°)"
                
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
                
                if wind_dir_text:
                    message += f"• Напрям вітру: {wind_dir_text}\n"
                
                if sunrise_time and sunset_time:
                    message += f"• Сонце: {sunrise_time} - {sunset_time}\n"
                
                # Додаємо почасовий прогноз для кожного дня
                hourly_section = self._format_hourly_forecast_for_day(weather_data, i)
                if hourly_section:
                    message += hourly_section
                
                # Додаємо вітер на висотах (однаковий для всіх днів, бо беремо поточні дані)
                altitude_section = self._format_altitude_wind(weather_data.get('altitude_wind', []))
                if altitude_section:
                    message += altitude_section
                
                message += f"\n📡 *Джерело:* Open-Meteo API"
                
                messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error formatting 3-day forecast: {e}", exc_info=True)
            return []
    
    def _format_hourly_forecast(self, weather_data: dict) -> str:
        """Форматувати почасовий прогноз для поточної погоди"""
        return self._format_hourly_forecast_for_day(weather_data, day_index=0)
    
    def _format_hourly_forecast_for_day(self, weather_data: dict, day_index: int = 0) -> str:
        """Форматувати почасовий прогноз для конкретного дня"""
        try:
            hourly = weather_data.get('hourly', {})
            
            if 'time' not in hourly or len(hourly['time']) == 0:
                return ""
            
            # Визначаємо години для дня
            hours_per_day = 24
            start_hour = day_index * hours_per_day
            
            # Беремо наступні 6 годин
            current_hour = datetime.now().hour if day_index == 0 else 0
            forecast_hours = []
            
            for i in range(start_hour, min(start_hour + hours_per_day, len(hourly['time']))):
                try:
                    time_str = hourly['time'][i]
                    hour = int(time_str.split('T')[1].split(':')[0])
                    
                    if day_index == 0:
                        if hour >= current_hour and len(forecast_hours) < 6:
                            forecast_hours.append({
                                'hour': hour,
                                'temp': hourly.get('temperature_2m', [0])[i] if i < len(hourly.get('temperature_2m', [])) else 0,
                                'precip_prob': hourly.get('precipitation_probability', [0])[i] if i < len(hourly.get('precipitation_probability', [])) else 0,
                                'precipitation': hourly.get('precipitation', [0])[i] if i < len(hourly.get('precipitation', [])) else 0,
                                'weather_code': hourly.get('weather_code', [0])[i] if i < len(hourly.get('weather_code', [])) else 0,
                                'wind_speed': hourly.get('wind_speed_10m', [0])[i] if i < len(hourly.get('wind_speed_10m', [])) else 0,
                                'wind_direction': hourly.get('wind_direction_10m', [0])[i] if i < len(hourly.get('wind_direction_10m', [])) else 0,
                            })
                    else:
                        if 8 <= hour <= 20 and len(forecast_hours) < 6:
                            forecast_hours.append({
                                'hour': hour,
                                'temp': hourly.get('temperature_2m', [0])[i] if i < len(hourly.get('temperature_2m', [])) else 0,
                                'precip_prob': hourly.get('precipitation_probability', [0])[i] if i < len(hourly.get('precipitation_probability', [])) else 0,
                                'precipitation': hourly.get('precipitation', [0])[i] if i < len(hourly.get('precipitation', [])) else 0,
                                'weather_code': hourly.get('weather_code', [0])[i] if i < len(hourly.get('weather_code', [])) else 0,
                                'wind_speed': hourly.get('wind_speed_10m', [0])[i] if i < len(hourly.get('wind_speed_10m', [])) else 0,
                                'wind_direction': hourly.get('wind_direction_10m', [0])[i] if i < len(hourly.get('wind_direction_10m', [])) else 0,
                            })
                except Exception as e:
                    logger.error(f"❌ Error parsing hour: {e}")
                    continue
            
            if not forecast_hours:
                return ""
            
            # Форматуємо почасовий прогноз
            message = "\n⏰ *Почасовий прогноз:*\n"
            
            for forecast in forecast_hours:
                emoji = self.get_weather_emoji(forecast['weather_code'])
                wind_dir_text = self.get_wind_direction(forecast.get('wind_direction', 0))
                
                precip_info = ""
                if forecast['precip_prob'] > 0:
                    precip_info = f", {forecast['precip_prob']}% опади"
                    if forecast['precipitation'] > 0:
                        precip_info += f" ({forecast['precipitation']:.1f} мм)"
                
                message += f"• {forecast['hour']:02d}:00 - {emoji} {forecast['temp']:.0f}°C{precip_info}, "
                message += f"вітер {forecast['wind_speed']:.1f} м/с ({wind_dir_text})\n"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error formatting hourly forecast: {e}")
            return ""
    
    def _format_altitude_wind(self, wind_data: List[Dict]) -> str:
        """Форматувати вітер на висотах"""
        if not wind_data:
            # Якщо немає даних, повертаємо примітку
            return "\n💨 *Вітер на висотах:*\nДані тимчасово недоступні\n"
        
        message = "\n💨 *Вітер на висотах:*\n"
        
        # Сортуємо за висотою
        sorted_data = sorted(wind_data, key=lambda x: x['altitude'])
        
        for data in sorted_data:
            altitude = data['altitude']
            level_name = data.get('level', '')
            speed = data['speed']
            direction = data['direction']
            direction_text = data.get('direction_text', self.get_wind_direction(direction))
            
            message += f"• ~{altitude}м ({level_name}): {direction_text} "
            message += f"({direction:.0f}°) {speed:.1f} м/с\n"
        
        message += "\nℹ️ *Примітка:* Дані з Open-Meteo API\n"
        
        return message
    
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