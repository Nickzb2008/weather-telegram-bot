import requests
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
import re

logger = logging.getLogger(__name__)

class WeatherAPI:
    def __init__(self):
        self.open_meteo_url = "https://api.open-meteo.com/v1/forecast"
        self.weather_gov_url = "https://api.weather.gov"
        
        # Цільові висоти для відображення
        self.target_altitudes = [400, 600, 800, 1000]  # метри
        
        # Маппінг висот Open-Meteo до наших цільових висот
        self.open_meteo_altitude_map = {
            '80m': 400,   # ~400м
            '100m': 600,  # ~600м
            '120m': 800,  # ~800м
            '180m': 1000  # ~1000м
        }
    
    def get_weather(self, lat: float, lon: float, forecast_days: int = 3) -> Optional[dict]:
        """Отримати погоду з Open-Meteo API з даними про вітер на висотах"""
        logger.info(f"🌤 Getting weather for lat={lat}, lon={lon}, days={forecast_days}")
        
        try:
            # Запит з максимальною кількістю параметрів для висотного вітру
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
                    # Земний вітер
                    'wind_speed_10m', 'wind_direction_10m',
                    # Вітер на висотах (Open-Meteo)
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
            
            logger.info(f"🌍 Requesting Open-Meteo data...")
            
            response = requests.get(self.open_meteo_url, params=params, timeout=20)
            logger.info(f"📡 Open-Meteo response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Open-Meteo data received successfully")
                
                # Перевіряємо, чи отримали дані про висотний вітер
                hourly = data.get('hourly', {})
                has_altitude_wind = any(key in hourly for key in ['wind_speed_80m', 'wind_speed_100m'])
                
                if has_altitude_wind:
                    logger.info("✅ Found altitude wind data in Open-Meteo response")
                    # Екстрактуємо дані про висотний вітер
                    altitude_wind_data = self._extract_open_meteo_altitude_wind(data)
                else:
                    logger.warning("⚠️ No altitude wind data in Open-Meteo, using estimation")
                    # Якщо немає даних про висотний вітер, використовуємо апроксимацію
                    altitude_wind_data = self._estimate_altitude_wind_from_surface(data)
                
                # Додаємо дані про висотний вітер до основного об'єкта
                if altitude_wind_data:
                    data['altitude_wind'] = altitude_wind_data
                    logger.info(f"✅ Added wind data for {len(altitude_wind_data)} altitude levels")
                else:
                    logger.warning("⚠️ Could not get any altitude wind data")
                    data['altitude_wind'] = []
                
                return data
            else:
                logger.error(f"❌ Open-Meteo API error: {response.status_code}")
                # Спрощений запит як запасний варіант
                return self._get_fallback_weather(lat, lon, forecast_days)
                
        except Exception as e:
            logger.error(f"❌ Error getting weather data: {e}", exc_info=True)
            return self._get_fallback_weather(lat, lon, forecast_days)
    
    def _get_fallback_weather(self, lat: float, lon: float, forecast_days: int = 3) -> Optional[dict]:
        """Запасний варіант зі спрощеним запитом"""
        try:
            logger.info("🔄 Trying fallback weather request")
            
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
            
            response = requests.get(self.open_meteo_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Fallback weather data received")
                
                # Оцінюємо висотний вітер на основі земного
                altitude_wind_data = self._estimate_altitude_wind_from_surface(data)
                data['altitude_wind'] = altitude_wind_data if altitude_wind_data else []
                
                return data
            
        except Exception as e:
            logger.error(f"❌ Fallback request error: {e}")
        
        return None
    
    def _extract_open_meteo_altitude_wind(self, weather_data: dict) -> List[Dict]:
        """Витягти дані про вітер на висотах з відповіді Open-Meteo"""
        try:
            hourly = weather_data.get('hourly', {})
            if not hourly or 'time' not in hourly:
                logger.warning("⚠️ No hourly data available")
                return []
            
            # Визначаємо поточну годину для отримання актуальних даних
            current_hour = datetime.now().hour
            hour_index = min(current_hour, len(hourly['time']) - 1) if hourly['time'] else 0
            
            logger.info(f"⏰ Using hour index {hour_index} (current hour: {current_hour})")
            
            wind_data = []
            
            # Перевіряємо кожну висоту Open-Meteo
            for om_level, target_altitude in self.open_meteo_altitude_map.items():
                speed_key = f'wind_speed_{om_level}'
                dir_key = f'wind_direction_{om_level}'
                
                if speed_key in hourly and dir_key in hourly:
                    if len(hourly[speed_key]) > hour_index and len(hourly[dir_key]) > hour_index:
                        speed = hourly[speed_key][hour_index]
                        direction = hourly[dir_key][hour_index]
                        
                        if speed is not None and direction is not None:
                            wind_data.append({
                                'altitude': target_altitude,
                                'source_altitude': om_level,
                                'speed': float(speed),
                                'direction': float(direction),
                                'source': 'Open-Meteo',
                                'hour_index': hour_index
                            })
                            logger.info(f"✅ Extracted wind at {target_altitude}m: {speed:.1f} m/s, {direction:.0f}°")
                        else:
                            logger.warning(f"⚠️ Null data for {target_altitude}m")
                    else:
                        logger.warning(f"⚠️ Insufficient data for {target_altitude}m")
                else:
                    logger.warning(f"⚠️ Keys missing for {target_altitude}m: {speed_key}, {dir_key}")
            
            # Сортуємо за висотою
            wind_data.sort(key=lambda x: x['altitude'])
            
            return wind_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting altitude wind: {e}", exc_info=True)
            return []
    
    def _estimate_altitude_wind_from_surface(self, weather_data: dict) -> List[Dict]:
        """Оцінити вітер на висотах на основі земного вітру"""
        try:
            current = weather_data.get('current', {})
            wind_speed_10m = current.get('wind_speed_10m', 0)
            wind_dir_10m = current.get('wind_direction_10m', 0)
            
            if wind_speed_10m is None or wind_dir_10m is None:
                logger.warning("⚠️ No surface wind data for estimation")
                return []
            
            logger.info(f"🌬 Estimating from surface: {wind_speed_10m:.1f} m/s, {wind_dir_10m:.0f}°")
            
            wind_data = []
            
            # Метод логарифмічного профілю вітру для приземного шару атмосфери
            # Формула: U(z) = U10 * ln(z/z0) / ln(10/z0)
            # де z0 - параметр шорсткості (приймаємо 0.1 для відкритої місцевості)
            z0 = 0.1  # параметр шорсткості (метри)
            
            for target_altitude in self.target_altitudes:
                # Обчислюємо коефіцієнт посилення швидкості
                if wind_speed_10m > 0:
                    # Логарифмічний закон
                    u_ratio = math.log(target_altitude / z0) / math.log(10 / z0)
                    altitude_speed = wind_speed_10m * u_ratio
                else:
                    altitude_speed = 0
                
                # Невелика корекція напряму з висотою (експеріментально)
                # На великих висотах вітер зазвичай повертає праворуч (ефект Коріоліса)
                direction_change = (target_altitude / 1000) * 10  # до 10° на 1000м
                altitude_direction = (wind_dir_10m + direction_change) % 360
                
                wind_data.append({
                    'altitude': target_altitude,
                    'speed': max(0, altitude_speed),  # переконуємось, що не від'ємне
                    'direction': altitude_direction,
                    'source': 'Estimation',
                    'surface_speed': wind_speed_10m,
                    'surface_direction': wind_dir_10m,
                    'method': 'logarithmic_profile'
                })
            
            return wind_data
            
        except Exception as e:
            logger.error(f"❌ Error estimating altitude wind: {e}")
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
            
            # Вказуємо джерело даних про висотний вітер
            wind_sources = []
            for wind_data in weather_data.get('altitude_wind', []):
                source = wind_data.get('source', '')
                if source and source not in wind_sources:
                    wind_sources.append(source)
            
            if wind_sources:
                if 'Estimation' in wind_sources:
                    message += " (висотний вітер - апроксимація)"
                elif 'Open-Meteo' in wind_sources:
                    message += " (висотний вітер - Open-Meteo)"
            
            message += f"\n🔄 *Оновлено:* {datetime.now().strftime('%H:%M %d.%m.%Y')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting current weather: {e}", exc_info=True)
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
                
                # Додаємо вітер на висотах (використовуємо поточні дані для всіх днів)
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
            return "\n💨 *Вітер на висотах:*\nДані тимчасово недоступні\n"
        
        message = "\n💨 *Вітер на висотах:*\n"
        
        # Сортуємо за висотою
        sorted_data = sorted(wind_data, key=lambda x: x['altitude'])
        
        for data in sorted_data:
            altitude = data['altitude']
            speed = data['speed']
            direction = data['direction']
            source = data.get('source', 'Unknown')
            direction_text = self.get_wind_direction(direction)
            
            message += f"• ~{altitude}м: {direction_text} "
            message += f"({direction:.0f}°) {speed:.1f} м/с"
            
            # Додаємо інформацію про джерело, якщо це апроксимація
            if source == 'Estimation':
                surface_speed = data.get('surface_speed', 0)
                surface_dir = data.get('surface_direction', 0)
                message += f" [апроксимація з {surface_speed:.1f} м/с на землі]"
            
            message += "\n"
        
        # Додаємо загальну примітку
        sources = set(data.get('source', '') for data in sorted_data)
        if 'Estimation' in sources:
            message += "\nℹ️ *Примітка:* Висотний вітер апроксимовано на основі земного\n"
            message += "за логарифмічним законом профілю вітру.\n"
        elif 'Open-Meteo' in sources:
            message += "\nℹ️ *Примітка:* Дані про висотний вітер з Open-Meteo API\n"
        
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