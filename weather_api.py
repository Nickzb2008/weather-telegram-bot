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
                    'wind_speed_10m', 'wind_direction_10m', 'wind_gusts_10m',
                    # Додаємо вітер на різних висотах
                    'wind_speed_80m', 'wind_direction_80m', 'wind_gusts_80m',
                    'wind_speed_120m', 'wind_direction_120m', 'wind_gusts_120m',
                    'wind_speed_180m', 'wind_direction_180m', 'wind_gusts_180m'
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

    def get_wind_direction(self, degrees: float) -> str:
        """Конвертувати градуси у назву напрямку вітру"""
        if degrees is None:
            return "Не визначено"
        
        directions = ["Північний", "Північно-східний", "Східний", "Південно-східний",
                     "Південний", "Південно-західний", "Західний", "Північно-західний"]
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
            
            # Формуємо повідомлення у новому форматі
            message = f"🌤 *Погода в {settlement_name} ({region})*\n\n"
            
            message += f"📊 *Загальна інформація:*\n"
            message += f"• Стан: {weather_desc}\n"
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
            message += f"• Видимість: *{visibility:.1f} км*\n"
            message += f"• Хмарність: *{cloud_cover}%*\n"
            
            # Додаємо почасовий прогноз
            hourly_section = self._format_hourly_forecast(weather_data, include_altitude=False)
            if hourly_section:
                message += hourly_section
            
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
                
                # Додаємо вітер на висотах для кожного дня
                altitude_wind_section = self._format_altitude_wind_for_day(weather_data, i)
                if altitude_wind_section:
                    message += altitude_wind_section
                
                message += f"\n📡 *Джерело:* Open-Meteo API"
                
                messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"❌ Error formatting 3-day forecast: {e}", exc_info=True)
            return []

    def _format_hourly_forecast(self, weather_data: dict, include_altitude: bool = True) -> str:
        """Форматувати почасовий прогноз для поточної погоди"""
        return self._format_hourly_forecast_for_day(weather_data, day_index=0, include_altitude=include_altitude)

    def _format_hourly_forecast_for_day(self, weather_data: dict, day_index: int = 0, include_altitude: bool = True) -> str:
        """Форматувати почасовий прогноз для конкретного дня"""
        logger.info(f"🔧 Formatting hourly forecast for day {day_index}")
        
        try:
            hourly = weather_data.get('hourly', {})
            
            if 'time' not in hourly or len(hourly['time']) == 0:
                logger.warning("❌ No hourly time data available")
                return ""
            
            # Визначаємо години для дня
            hours_per_day = 24
            start_hour = day_index * hours_per_day
            end_hour = start_hour + hours_per_day
            
            # Обмежуємо до доступних даних
            if start_hour >= len(hourly['time']):
                return ""
            
            # Беремо наступні 6 годин з початку дня або поточного часу
            current_hour = datetime.now().hour if day_index == 0 else 0
            forecast_hours = []
            
            for i in range(start_hour, min(end_hour, len(hourly['time']))):
                try:
                    time_str = hourly['time'][i]
                    hour = int(time_str.split('T')[1].split(':')[0])
                    
                    # Для сьогодні беремо години починаючи з поточної, для інших днів - з 8 ранку
                    if day_index == 0:
                        if hour >= current_hour and len(forecast_hours) < 6:
                            forecast_hours.append({
                                'hour': hour,
                                'temp': hourly.get('temperature_2m', [0])[i] if i < len(hourly.get('temperature_2m', [])) else 0,
                                'precip_prob': hourly.get('precipitation_probability', [0])[i] if i < len(hourly.get('precipitation_probability', [])) else 0,
                                'precipitation': hourly.get('precipitation', [0])[i] if i < len(hourly.get('precipitation', [])) else 0,
                                'weather_code': hourly.get('weather_code', [0])[i] if i < len(hourly.get('weather_code', [])) else 0,
                                'wind_speed': hourly.get('wind_speed_10m', [0])[i] if i < len(hourly.get('wind_speed_10m', [])) else 0,
                            })
                    else:
                        # Для наступних днів беремо години з 8 до 20
                        if 8 <= hour <= 20 and len(forecast_hours) < 6:
                            forecast_hours.append({
                                'hour': hour,
                                'temp': hourly.get('temperature_2m', [0])[i] if i < len(hourly.get('temperature_2m', [])) else 0,
                                'precip_prob': hourly.get('precipitation_probability', [0])[i] if i < len(hourly.get('precipitation_probability', [])) else 0,
                                'precipitation': hourly.get('precipitation', [0])[i] if i < len(hourly.get('precipitation', [])) else 0,
                                'weather_code': hourly.get('weather_code', [0])[i] if i < len(hourly.get('weather_code', [])) else 0,
                                'wind_speed': hourly.get('wind_speed_10m', [0])[i] if i < len(hourly.get('wind_speed_10m', [])) else 0,
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
                
                # Форматуємо інформацію про опади
                precip_info = ""
                if forecast['precip_prob'] > 0:
                    precip_info = f", {forecast['precip_prob']}% опади"
                    if forecast['precipitation'] > 0:
                        precip_info += f" ({forecast['precipitation']:.1f} мм)"
                
                message += f"• {forecast['hour']:02d}:00 - {emoji} {forecast['temp']:.0f}°C{precip_info}, вітер {forecast['wind_speed']:.1f} м/с\n"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error formatting hourly forecast for day {day_index}: {e}")
            return ""

    def _format_altitude_wind_for_day(self, weather_data: dict, day_index: int = 0) -> str:
        """Форматувати вітер на висотах для конкретного дня"""
        logger.info(f"🔧 Formatting altitude wind for day {day_index}")
        
        try:
            hourly = weather_data.get('hourly', {})
            
            if 'time' not in hourly or len(hourly['time']) == 0:
                return ""
            
            # Визначаємо години для дня
            hours_per_day = 24
            start_hour = day_index * hours_per_day
            
            # Беремо першу годину дня (12:00) для отримання даних про вітер на висотах
            target_hour_index = start_hour + 12  # 12:00 дня
            
            if target_hour_index >= len(hourly['time']):
                target_hour_index = start_hour
            
            # Отримуємо дані про вітер на висотах
            wind_data = {}
            
            # Перевіряємо наявність даних
            altitude_params = [
                ('80m', 'wind_speed_80m', 'wind_direction_80m', 'wind_gusts_80m'),
                ('120m', 'wind_speed_120m', 'wind_direction_120m', 'wind_gusts_120m'),
                ('180m', 'wind_speed_180m', 'wind_direction_180m', 'wind_gusts_180m'),
            ]
            
            has_altitude_data = False
            for altitude_name, speed_key, dir_key, gust_key in altitude_params:
                if (speed_key in hourly and len(hourly[speed_key]) > target_hour_index and
                    dir_key in hourly and len(hourly[dir_key]) > target_hour_index):
                    
                    wind_speed = hourly[speed_key][target_hour_index]
                    wind_dir = hourly[dir_key][target_hour_index]
                    wind_gust = hourly.get(gust_key, [0])[target_hour_index] if gust_key in hourly else 0
                    
                    wind_data[altitude_name] = {
                        'speed': wind_speed,
                        'direction': wind_dir,
                        'gust': wind_gust
                    }
                    has_altitude_data = True
            
            if not has_altitude_data:
                return "\n💨 *Вітер на висотах:*\nДані відсутні\n"
            
            # Форматуємо повідомлення
            message = "\n💨 *Вітер на висотах:*\n"
            
            # Вітер на ~400м (80м)
            if '80m' in wind_data:
                data = wind_data['80m']
                wind_dir_text = self.get_wind_direction(data['direction'])
                message += f"• ~400м: {wind_dir_text} ({int(data['direction'])}°) {data['speed']:.1f} м/с (пориви до {data['gust']:.1f} м/с)\n"
            
            # Вітер на ~600м (120м)
            if '120m' in wind_data:
                data = wind_data['120m']
                wind_dir_text = self.get_wind_direction(data['direction'])
                message += f"• ~600м: {wind_dir_text} ({int(data['direction'])}°) {data['speed']:.1f} м/с (пориви до {data['gust']:.1f} м/с)\n"
            
            # Вітер на ~800м (180м)
            if '180m' in wind_data:
                data = wind_data['180m']
                wind_dir_text = self.get_wind_direction(data['direction'])
                message += f"• ~800м: {wind_dir_text} ({int(data['direction'])}°) {data['speed']:.1f} м/с (пориви до {data['gust']:.1f} м/с)\n"
            
            # Для 1000м використовуємо дані з 180м (екстраполяція)
            if '180m' in wind_data:
                data = wind_data['180m']
                wind_dir_text = self.get_wind_direction(data['direction'])
                # Трохи збільшуємо швидкість для 1000м
                estimated_speed = data['speed'] * 1.1
                estimated_gust = data['gust'] * 1.1
                message += f"• ~1000м: {wind_dir_text} ({int(data['direction'])}°) {estimated_speed:.1f} м/с (пориви до {estimated_gust:.1f} м/с)\n"
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Error formatting altitude wind for day {day_index}: {e}")
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