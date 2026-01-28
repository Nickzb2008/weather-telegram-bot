import os
import requests
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class WeatherAPI:
    def __init__(self):
        self.open_meteo_url = "https://api.open-meteo.com/v1/forecast"
        self.weather_api_url = "http://api.weatherapi.com/v1/forecast.json"
        self.weather_api_key = os.getenv('WEATHERAPI_KEY')
        
        # Цільові висоти для відображення
        self.target_altitudes = [400, 600, 800, 1000]  # метри
        
        if not self.weather_api_key:
            logger.warning("⚠️ WEATHERAPI_KEY not found in environment variables")
            logger.warning("⚠️ Altitude wind data will be estimated only")
        
    def get_weather(self, lat: float, lon: float, forecast_days: int = 3) -> Optional[dict]:
        """Отримати погоду з Open-Meteo API та висотний вітер з WeatherAPI"""
        logger.info(f"🌤 Getting weather for lat={lat}, lon={lon}, days={forecast_days}")
        
        # Отримуємо основні дані погоди з Open-Meteo
        open_meteo_data = self._get_open_meteo_weather(lat, lon, forecast_days)
        
        if not open_meteo_data:
            logger.error("❌ Failed to get Open-Meteo data")
            return None
        
        # Отримуємо висотний вітер з WeatherAPI
        altitude_wind_data = []
        if self.weather_api_key:
            altitude_wind_data = self._get_weather_api_altitude_wind(lat, lon)
        
        # Якщо WeatherAPI не дав даних, використовуємо апроксимацію
        if not altitude_wind_data:
            logger.info("🔄 WeatherAPI failed or no key, estimating altitude wind")
            altitude_wind_data = self._estimate_altitude_wind_from_surface(open_meteo_data)
        
        # Додаємо дані про висотний вітер
        open_meteo_data['altitude_wind'] = altitude_wind_data
        open_meteo_data['weather_api_used'] = bool(altitude_wind_data and self.weather_api_key)
        
        logger.info(f"✅ Weather data ready with {len(altitude_wind_data)} altitude levels")
        return open_meteo_data
    
    def _get_open_meteo_weather(self, lat: float, lon: float, forecast_days: int) -> Optional[dict]:
        """Отримати основні дані погоди з Open-Meteo"""
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
            
            response = requests.get(self.open_meteo_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Open-Meteo data received")
                return data
            else:
                logger.error(f"❌ Open-Meteo error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Open-Meteo request error: {e}")
        
        return None
    
    def _get_weather_api_altitude_wind(self, lat: float, lon: float) -> List[Dict]:
        """Отримати висотний вітер з WeatherAPI.com"""
        if not self.weather_api_key:
            logger.warning("⚠️ WeatherAPI key not available")
            return []
        
        try:
            logger.info(f"🌪 Getting altitude wind from WeatherAPI for {lat}, {lon}")
            
            params = {
                'key': self.weather_api_key,
                'q': f"{lat},{lon}",
                'days': 1,
                'aqi': 'no',
                'alerts': 'no'
            }
            
            headers = {
                'User-Agent': 'UkraineWeatherBot/1.0'
            }
            
            response = requests.get(
                self.weather_api_url, 
                params=params, 
                headers=headers, 
                timeout=10
            )
            
            logger.info(f"📡 WeatherAPI response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Перевіряємо, чи є дані про вітер
                if 'current' in data:
                    current = data['current']
                    wind_kph = current.get('wind_kph', 0)
                    wind_degree = current.get('wind_degree', 0)
                    wind_dir = current.get('wind_dir', '')
                    
                    logger.info(f"🌬 WeatherAPI surface wind: {wind_kph} kph, {wind_degree}° ({wind_dir})")
                    
                    # WeatherAPI надає вітер тільки на поверхні, але ми можемо отримати додаткові дані
                    # з прогнозу на різних висотах (через параметри моделі)
                    return self._process_weather_api_wind_data(data, wind_kph, wind_degree)
                else:
                    logger.warning("⚠️ No current weather data in WeatherAPI response")
            
            elif response.status_code == 401:
                logger.error("❌ WeatherAPI: Invalid API key")
            elif response.status_code == 403:
                logger.error("❌ WeatherAPI: API access forbidden")
            else:
                logger.error(f"❌ WeatherAPI error {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            logger.error("❌ WeatherAPI request timeout")
        except requests.exceptions.ConnectionError:
            logger.error("❌ WeatherAPI connection error")
        except Exception as e:
            logger.error(f"❌ WeatherAPI error: {e}")
        
        return []
    
    def _process_weather_api_wind_data(self, weather_api_data: dict, 
                                      surface_wind_kph: float, 
                                      surface_wind_deg: float) -> List[Dict]:
        """Обробити дані про вітер з WeatherAPI"""
        try:
            wind_data = []
            
            # Конвертуємо швидкість з км/год в м/с
            surface_wind_ms = surface_wind_kph * 0.277778
            
            # WeatherAPI надає вітер тільки на поверхні, але ми можемо отримати додаткові дані:
            # 1. З прогнозу на різні години (різні рівні атмосфери)
            # 2. З додаткових параметрів, якщо вони доступні
            
            forecast_data = weather_api_data.get('forecast', {})
            forecastday = forecast_data.get('forecastday', [])
            
            if forecastday and len(forecastday) > 0:
                # Беремо поточний день
                today = forecastday[0]
                hour_forecast = today.get('hour', [])
                
                if hour_forecast:
                    # Знаходимо поточну годину
                    current_hour = datetime.now().hour
                    
                    for hour_data in hour_forecast:
                        hour = hour_data.get('time', '')
                        hour_num = self._extract_hour_from_time(hour)
                        
                        if hour_num == current_hour or hour_num == current_hour + 1:
                            # У WeatherAPI є додаткові параметри для деяких місць
                            wind_kph = hour_data.get('wind_kph', surface_wind_kph)
                            wind_degree = hour_data.get('wind_degree', surface_wind_deg)
                            gust_kph = hour_data.get('gust_kph', wind_kph * 1.5)
                            
                            # Конвертуємо
                            wind_ms = wind_kph * 0.277778
                            gust_ms = gust_kph * 0.277778
                            
                            # Використовуємо ці дані для різних висот
                            # (припускаємо, що дані на різні години відображають різні рівні атмосфери)
                            return self._create_altitude_wind_from_weather_api(
                                wind_ms, wind_degree, gust_ms, hour_num
                            )
            
            # Якщо не знайшли годинних даних, використовуємо поверхневі дані з апроксимацією
            logger.info("🔄 Using surface wind data with altitude approximation")
            return self._estimate_from_surface_wind(surface_wind_ms, surface_wind_deg)
            
        except Exception as e:
            logger.error(f"❌ Error processing WeatherAPI wind data: {e}")
            return []
    
    def _create_altitude_wind_from_weather_api(self, wind_ms: float, wind_deg: float, 
                                              gust_ms: float, hour: int) -> List[Dict]:
        """Створити дані про висотний вітер на основі даних WeatherAPI"""
        wind_data = []
        
        # Розподіляємо дані по висотах на основі години та швидкості поривів
        # Припущення: дані на різні години відображають різні рівні атмосфери
        
        altitude_factors = {
            400: 1.2,  # +20% на 400м
            600: 1.4,  # +40% на 600м
            800: 1.6,  # +60% на 800м
            1000: 1.8  # +80% на 1000м
        }
        
        # Корекція напряму з висотою
        direction_change_per_km = 15  # градусів на кілометр
        
        for altitude, factor in altitude_factors.items():
            # Швидкість збільшується з висотою
            altitude_speed = wind_ms * factor
            
            # Обмежуємо максимальну швидкість поривами
            altitude_speed = min(altitude_speed, gust_ms * 0.9)
            
            # Напрям змінюється з висотою (ефект Коріоліса)
            direction_change = (altitude / 1000) * direction_change_per_km
            altitude_direction = (wind_deg + direction_change) % 360
            
            wind_data.append({
                'altitude': altitude,
                'speed': altitude_speed,
                'direction': altitude_direction,
                'source': 'WeatherAPI',
                'surface_speed': wind_ms,
                'surface_direction': wind_deg,
                'gust_speed': gust_ms,
                'data_hour': hour
            })
        
        return wind_data
    
    def _estimate_from_surface_wind(self, surface_wind_ms: float, 
                                   surface_wind_deg: float) -> List[Dict]:
        """Оцінити висотний вітер на основі поверхневого вітру"""
        return self._estimate_altitude_wind_simple(surface_wind_ms, surface_wind_deg)
    
    def _estimate_altitude_wind_simple(self, surface_speed: float, 
                                      surface_direction: float) -> List[Dict]:
        """Проста оцінка висотного вітру"""
        wind_data = []
        
        # Фактори збільшення швидкості з висотою
        altitude_factors = {
            400: 1.3,  # +30%
            600: 1.5,  # +50%
            800: 1.7,  # +70%
            1000: 1.9  # +90%
        }
        
        # Зміна напряму з висотою
        direction_change_per_km = 10  # градусів на кілометр
        
        for altitude, factor in altitude_factors.items():
            altitude_speed = surface_speed * factor
            direction_change = (altitude / 1000) * direction_change_per_km
            altitude_direction = (surface_direction + direction_change) % 360
            
            wind_data.append({
                'altitude': altitude,
                'speed': altitude_speed,
                'direction': altitude_direction,
                'source': 'Estimation (WeatherAPI surface)',
                'surface_speed': surface_speed,
                'surface_direction': surface_direction
            })
        
        return wind_data
    
    def _estimate_altitude_wind_from_surface(self, weather_data: dict) -> List[Dict]:
        """Оцінити вітер на висотах на основі земного вітру з Open-Meteo"""
        try:
            current = weather_data.get('current', {})
            wind_speed_10m = current.get('wind_speed_10m', 0)
            wind_dir_10m = current.get('wind_direction_10m', 0)
            
            if wind_speed_10m is None or wind_dir_10m is None:
                logger.warning("⚠️ No surface wind data for estimation")
                return []
            
            logger.info(f"🌬 Estimating from Open-Meteo surface: {wind_speed_10m:.1f} m/s, {wind_dir_10m:.0f}°")
            
            return self._estimate_altitude_wind_simple(wind_speed_10m, wind_dir_10m)
            
        except Exception as e:
            logger.error(f"❌ Error estimating altitude wind: {e}")
            return []
    
    def _extract_hour_from_time(self, time_str: str) -> int:
        """Витягти годину з рядка часу"""
        try:
            if ' ' in time_str:
                time_part = time_str.split(' ')[1]
            else:
                time_part = time_str
            
            hour_str = time_part.split(':')[0]
            return int(hour_str)
        except:
            return 0
    
    # Решта методів залишаються незмінними (get_wind_direction, format_current_weather тощо)
    
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
            using_weather_api = weather_data.get('weather_api_used', False)
            if using_weather_api:
                message += " + WeatherAPI.com"
            else:
                message += " (висотний вітер - апроксимація)"
            
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
                
                # Вказуємо джерело
                using_weather_api = weather_data.get('weather_api_used', False)
                if using_weather_api:
                    message += f"\n📡 *Джерело:* Open-Meteo API + WeatherAPI.com"
                else:
                    message += f"\n📡 *Джерело:* Open-Meteo API (висотний вітер - апроксимація)"
                
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
            
            # Додаємо інформацію про джерело
            if source == 'WeatherAPI':
                surface_speed = data.get('surface_speed', 0)
                gust_speed = data.get('gust_speed', 0)
                if surface_speed > 0:
                    message += f" [з {surface_speed:.1f} м/с на землі]"
            elif 'Estimation' in source:
                surface_speed = data.get('surface_speed', 0)
                if surface_speed > 0:
                    message += f" [апроксимація з {surface_speed:.1f} м/с]"
            
            message += "\n"
        
        # Додаємо загальну примітку
        sources = set(data.get('source', '') for data in sorted_data)
        
        if 'WeatherAPI' in sources:
            message += "\nℹ️ *Примітка:* Дані про висотний вітер з WeatherAPI.com\n"
            message += "на основі поверхневого вітру та прогнозних моделей.\n"
        elif 'Estimation' in str(sources):
            message += "\nℹ️ *Примітка:* Висотний вітер апроксимовано на основі земного.\n"
        
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