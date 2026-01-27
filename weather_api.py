import requests
import math
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class WeatherAPI:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_weather(self, lat: float, lon: float) -> Optional[dict]:
        """Отримати погоду з Open-Meteo API"""
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
                    'wind_speed_10m', 'wind_direction_10m',
                    'wind_speed_80m', 'wind_direction_80m',
                    'wind_speed_120m', 'wind_direction_120m',
                    'wind_speed_180m', 'wind_direction_180m',
                    'temperature_2m', 'relative_humidity_2m'
                ],
                'daily': [
                    'temperature_2m_max', 'temperature_2m_min',
                    'precipitation_sum', 'precipitation_hours',
                    'weather_code', 'sunrise', 'sunset'
                ],
                'timezone': 'auto',
                'forecast_days': 3
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Open-Meteo API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Open-Meteo error: {e}")
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
            0: "Ясне небо", 1: "Переважно ясно", 2: "Мінлива хмарність", 3: "Хмарно",
            45: "Туман", 48: "Покритий інеєм туман",
            51: "Легка мряка", 53: "Помірна мряка", 55: "Густа мряка",
            56: "Легка мряка, що замерзає", 57: "Густа мряка, що замерзає",
            61: "Невеликий дощ", 63: "Помірний дощ", 65: "Сильний дощ",
            66: "Дощ, що замерзає", 67: "Сильний дощ, що замерзає",
            71: "Невеликий снігопад", 73: "Помірний снігопад", 75: "Сильний снігопад",
            77: "Сніжинки", 80: "Невеликі зливи", 81: "Помірні зливи", 82: "Сильні зливи",
            85: "Невеликі снігові зливи", 86: "Сильні снігові зливи",
            95: "Гроза", 96: "Гроза з градом", 99: "Сильна гроза з градом"
        }
        return weather_codes.get(weather_code, "Невідомо")
    
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
    
    def format_weather_message(self, settlement_name: str, region: str, weather_data: dict) -> str:
        """Форматувати повідомлення з погодою"""
        try:
            current = weather_data.get('current', {})
            hourly = weather_data.get('hourly', {})
            daily = weather_data.get('daily', {})
            
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
            
            # Вітер на висотах
            current_hour = datetime.now().hour
            wind_at_heights = {}
            
            if 'time' in hourly and 'wind_speed_80m' in hourly:
                times = hourly['time']
                current_index = 0
                
                for i, time_str in enumerate(times):
                    try:
                        hour = int(time_str.split('T')[1].split(':')[0])
                        if hour == current_hour:
                            current_index = i
                            break
                    except:
                        continue
                
                # Вітер на різних висотах
                heights = [
                    ('400m', 'wind_speed_80m', 'wind_direction_80m', 0.7),
                    ('600m', 'wind_speed_80m', 'wind_direction_80m', 1.0),
                    ('800m', 'wind_speed_120m', 'wind_direction_120m', 1.0),
                    ('1000m', 'wind_speed_180m', 'wind_direction_180m', 1.0),
                ]
                
                for height_name, speed_key, dir_key, factor in heights:
                    if speed_key in hourly and dir_key in hourly:
                        speeds = hourly[speed_key]
                        dirs = hourly[dir_key]
                        if len(speeds) > current_index and len(dirs) > current_index:
                            wind_at_heights[height_name] = {
                                'speed': speeds[current_index] * factor,
                                'direction': dirs[current_index],
                                'height': height_name
                            }
            
            # Прогноз на наступні дні
            forecast_text = ""
            if 'time' in daily and len(daily['time']) > 1:
                forecast_text = "\n📅 *Прогноз на наступні дні:*\n"
                for i in range(1, min(3, len(daily['time']))):
                    date = daily['time'][i].split('T')[0]
                    max_temp = daily.get('temperature_2m_max', [0])[i]
                    min_temp = daily.get('temperature_2m_min', [0])[i]
                    precip = daily.get('precipitation_sum', [0])[i]
                    weather_code_day = daily.get('weather_code', [0])[i]
                    weather_desc_day = self.get_weather_description(weather_code_day)
                    
                    forecast_text += f"• {date}: {min_temp:.0f}°-{max_temp:.0f}°C, {weather_desc_day}"
                    if precip > 0:
                        forecast_text += f", {precip:.1f}мм опадів"
                    forecast_text += "\n"
            
            # Формуємо повідомлення
            message = f"🌤 *Погода в {settlement_name} ({region})*\n\n"
            
            message += f"📊 *Загальна інформація:*\n"
            message += f"• Стан: *{weather_desc}*\n"
            message += f"• Температура: *{temp:.1f}°C*\n"
            message += f"• Відчувається як: *{feels_like:.1f}°C*\n"
            message += f"• Вологість: *{humidity}%*\n"
            message += f"• Тиск: *{pressure:.0f} hPa*\n"
            message += f"• Видимість: *{visibility:.1f} км*\n\n"
            
            # Вітер на землі
            wind_dir_text = self.get_wind_direction(wind_dir_10m)
            message += f"💨 *Вітер на землі (10м):*\n"
            message += f"• Швидкість: *{wind_speed_10m:.1f} м/с*\n"
            message += f"• Пориви: *{wind_gusts_10m:.1f} м/с*\n"
            message += f"• Напрямок: *{wind_dir_text}*\n\n"
            
            # Вітер на висотах
            if wind_at_heights:
                message += f"🌀 *Вітер на висотах:*\n"
                for height in ['400m', '600m', '800m', '1000m']:
                    if height in wind_at_heights:
                        data = wind_at_heights[height]
                        wind_dir = self.get_wind_direction(data['direction'])
                        message += f"• {height}: *{data['speed']:.1f} м/с*, {wind_dir}\n"
                message += f"\n"
            
            # Опади
            message += f"🌧 *Опади (за годину):*\n"
            message += f"• Загальні: *{precipitation:.1f} мм*\n"
            message += f"• Дощ: *{rain:.1f} мм*\n"
            message += f"• Сніг: *{snowfall:.1f} мм*\n\n"
            
            # Хмарність
            message += f"☁️ *Хмарність:*\n"
            message += f"• Рівень: *{cloud_cover}%*\n"
            if cloud_base:
                message += f"• Нижня кромка хмар: *{cloud_base} м*\n"
            else:
                message += f"• Нижня кромка хмар: *Не визначено*\n"
            
            # Додаємо прогноз
            message += forecast_text
            
            message += f"\n📡 *Джерело:* Open-Meteo API\n"
            message += f"🔄 *Оновлено:* {datetime.now().strftime('%H:%M %d.%m.%Y')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting weather message: {e}")
            return None

# Глобальний екземпляр API погоди
weather_api = WeatherAPI()