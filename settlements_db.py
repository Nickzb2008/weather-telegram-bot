# settlements_db.py
import json
import os
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class UkraineSettlementsDB:
    def __init__(self):
        self.settlements = {}
        self._load_extended_database()
        logger.info(f"Завантажено {len(self.settlements)} населених пунктів")
    
    def _load_extended_database(self):
        """Завантаження розширеної бази населених пунктів України (міста + села)"""
        # Всі обласні центри України
        self._add_settlement("Київ", 50.4501, 30.5234, "Київська", "столиця", 2967000)
        self._add_settlement("Вінниця", 49.2328, 28.4816, "Вінницька", "обласний центр", 369000)
        self._add_settlement("Луцьк", 50.7472, 25.3254, "Волинська", "обласний центр", 217000)
        self._add_settlement("Дніпро", 48.4647, 35.0462, "Дніпропетровська", "обласний центр", 966000)
        self._add_settlement("Донецьк", 48.0159, 37.8028, "Донецька", "обласний центр", 901000)
        self._add_settlement("Житомир", 50.2547, 28.6587, "Житомирська", "обласний центр", 261000)
        self._add_settlement("Ужгород", 48.6208, 22.2879, "Закарпатська", "обласний центр", 115000)
        self._add_settlement("Запоріжжя", 47.8229, 35.1903, "Запорізька", "обласний центр", 722000)
        self._add_settlement("Івано-Франківськ", 48.9226, 24.7111, "Івано-Франківська", "обласний центр", 238000)
        self._add_settlement("Кропивницький", 48.5132, 32.2597, "Кіровоградська", "обласний центр", 222000)
        self._add_settlement("Львів", 49.8397, 24.0297, "Львівська", "обласний центр", 717000)
        self._add_settlement("Миколаїв", 46.9750, 31.9946, "Миколаївська", "обласний центр", 480000)
        self._add_settlement("Одеса", 46.4825, 30.7233, "Одеська", "обласний центр", 1017000)
        self._add_settlement("Полтава", 49.5883, 34.5514, "Полтавська", "обласний центр", 279000)
        self._add_settlement("Рівне", 50.6199, 26.2516, "Рівненська", "обласний центр", 246000)
        self._add_settlement("Суми", 50.9077, 34.7981, "Сумська", "обласний центр", 259000)
        self._add_settlement("Тернопіль", 49.5535, 25.5948, "Тернопільська", "обласний центр", 225000)
        self._add_settlement("Харків", 49.9935, 36.2304, "Харківська", "обласний центр", 1441000)
        self._add_settlement("Херсон", 46.6354, 32.6169, "Херсонська", "обласний центр", 283000)
        self._add_settlement("Хмельницький", 49.4220, 26.9841, "Хмельницька", "обласний центр", 274000)
        self._add_settlement("Черкаси", 49.4444, 32.0598, "Черкаська", "обласний центр", 269000)
        self._add_settlement("Чернівці", 48.2921, 25.9358, "Чернівецька", "обласний центр", 265000)
        self._add_settlement("Чернігів", 51.4982, 31.2893, "Чернігівська", "обласний центр", 286000)
        self._add_settlement("Луганськ", 48.5736, 39.3078, "Луганська", "обласний центр", 401000)
        self._add_settlement("Сімферополь", 44.9521, 34.1024, "АР Крим", "обласний центр", 332000)
        self._add_settlement("Севастополь", 44.6167, 33.5254, "АР Крим", "місто", 343000)
        
        # Додамо більше міст
        self._add_settlement("Кривий Ріг", 47.9105, 33.3918, "Дніпропетровська", "місто", 612000)
        self._add_settlement("Маріуполь", 47.0971, 37.5434, "Донецька", "місто", 431000)
        self._add_settlement("Макіївка", 48.0556, 38.0647, "Донецька", "місто", 344000)
        self._add_settlement("Горлівка", 48.3056, 38.0297, "Донецька", "місто", 242000)
        self._add_settlement("Кам'янське", 48.5076, 34.6132, "Дніпропетровська", "місто", 235000)
        self._add_settlement("Кременчук", 49.0667, 33.4167, "Полтавська", "місто", 217000)
        self._add_settlement("Мелітополь", 46.8489, 35.3653, "Запорізька", "місто", 150000)
        self._add_settlement("Краматорськ", 48.7392, 37.5839, "Донецька", "місто", 157000)
        self._add_settlement("Біла Церква", 49.7956, 30.1167, "Київська", "місто", 208000)
        self._add_settlement("Нікополь", 47.5667, 34.4000, "Дніпропетровська", "місто", 110000)
        self._add_settlement("Слов'янськ", 48.8531, 37.6050, "Донецька", "місто", 106000)
        self._add_settlement("Павлоград", 48.5200, 35.8700, "Дніпропетровська", "місто", 105000)
        self._add_settlement("Бердянськ", 46.7590, 36.7869, "Запорізька", "місто", 107000)
        
        # Додамо великі села та селища (понад 5 тис. населення)
        # Київська область
        self._add_settlement("Вишневе", 50.3869, 30.3639, "Київська", "місто", 39000)
        self._add_settlement("Ірпінь", 50.5167, 30.2500, "Київська", "місто", 60000)
        self._add_settlement("Буча", 50.5500, 30.2167, "Київська", "місто", 36000)
        self._add_settlement("Боярка", 50.3300, 30.2889, "Київська", "місто", 35000)
        self._add_settlement("Березань", 50.3194, 31.4700, "Київська", "місто", 16700)
        self._add_settlement("Українка", 50.1500, 30.7500, "Київська", "місто", 16000)
        self._add_settlement("Гостомель", 50.5833, 30.2667, "Київська", "селище", 17000)
        self._add_settlement("Ворзель", 50.5500, 30.1500, "Київська", "селище", 6500)
        self._add_settlement("Іванків", 50.9333, 29.9000, "Київська", "селище", 11000)
        self._add_settlement("Богуслав", 49.5467, 30.8744, "Київська", "місто", 16200)
        self._add_settlement("Васильків", 50.1778, 30.3219, "Київська", "місто", 37700)
        self._add_settlement("Вишгород", 50.5850, 30.5000, "Київська", "місто", 29800)
        self._add_settlement("Обухів", 50.1100, 30.6328, "Київська", "місто", 33200)
        self._add_settlement("Переяслав", 50.0650, 31.4450, "Київська", "місто", 27000)
        
        # Львівська область
        self._add_settlement("Стрий", 49.2553, 23.8506, "Львівська", "місто", 59000)
        self._add_settlement("Дрогобич", 49.3500, 23.5000, "Львівська", "місто", 74000)
        self._add_settlement("Червоноград", 50.3833, 24.2333, "Львівська", "місто", 65000)
        self._add_settlement("Самбір", 49.5167, 23.2000, "Львівська", "місто", 34000)
        self._add_settlement("Борислав", 49.2861, 23.4231, "Львівська", "місто", 33000)
        self._add_settlement("Трускавець", 49.2806, 23.5050, "Львівська", "місто", 29000)
        self._add_settlement("Новий Розділ", 49.4700, 24.1300, "Львівська", "місто", 28000)
        self._add_settlement("Золочів", 49.8053, 24.8933, "Львівська", "місто", 24000)
        self._add_settlement("Сокаль", 50.4833, 24.2833, "Львівська", "місто", 21000)
        self._add_settlement("Стебник", 49.3000, 23.5667, "Львівська", "місто", 21000)
        self._add_settlement("Гірник", 49.2333, 23.8667, "Львівська", "місто", 20000)
        self._add_settlement("Великі Мости", 50.2333, 24.1333, "Львівська", "селище", 5200)
        self._add_settlement("Жовква", 50.0667, 23.9667, "Львівська", "місто", 13500)
        self._add_settlement("Яворів", 49.9500, 23.3833, "Львівська", "місто", 13000)
        
        # Дніпропетровська область
        self._add_settlement("Жовті Води", 48.3500, 33.5167, "Дніпропетровська", "місто", 44400)
        self._add_settlement("Марганець", 47.6406, 34.6275, "Дніпропетровська", "місто", 46500)
        self._add_settlement("Підгородне", 48.5753, 35.0958, "Дніпропетровська", "місто", 19300)
        self._add_settlement("Першотравенськ", 48.3464, 36.4056, "Дніпропетровська", "місто", 28300)
        self._add_settlement("Синельникове", 48.3178, 35.5119, "Дніпропетровська", "місто", 30700)
        self._add_settlement("Тернівка", 48.5236, 36.0808, "Дніпропетровська", "місто", 29000)
        self._add_settlement("Апостолове", 47.6600, 33.7139, "Дніпропетровська", "місто", 14800)
        self._add_settlement("Верхньодніпровськ", 48.6564, 34.3281, "Дніпропетровська", "місто", 16400)
        self._add_settlement("Вільногірськ", 48.4794, 34.0181, "Дніпропетровська", "місто", 23500)
        self._add_settlement("Перещепине", 48.7367, 35.3608, "Дніпропетровська", "місто", 10000)
        
        # Додамо відомі села різних областей
        # Вінницька область
        self._add_settlement("Томашпіль", 48.5469, 28.5158, "Вінницька", "селище", 5600)
        self._add_settlement("Крижопіль", 48.3833, 28.8667, "Вінницька", "селище", 8500)
        self._add_settlement("Тульчин", 48.6750, 28.8481, "Вінницька", "місто", 15400)
        self._add_settlement("Немирів", 48.9767, 28.8436, "Вінницька", "місто", 11800)
        self._add_settlement("Погребище", 49.4833, 29.2667, "Вінницька", "місто", 9600)
        
        # Житомирська область
        self._add_settlement("Коростень", 50.9500, 28.6500, "Житомирська", "місто", 62000)
        self._add_settlement("Новоград-Волинський", 50.5833, 27.6333, "Житомирська", "місто", 56000)
        self._add_settlement("Малин", 50.7667, 29.2500, "Житомирська", "місто", 26900)
        self._add_settlement("Коростишів", 50.3167, 29.0667, "Житомирська", "місто", 25500)
        self._add_settlement("Овруч", 51.3247, 28.8072, "Житомирська", "місто", 16500)
        self._add_settlement("Радомишль", 50.4947, 29.2336, "Житомирська", "місто", 14700)
        self._add_settlement("Чуднів", 50.0500, 28.1167, "Житомирська", "селище", 6000)
        self._add_settlement("Ружин", 49.7167, 29.2167, "Житомирська", "селище", 4500)
        
        # Закарпатська область
        self._add_settlement("Мукачево", 48.4412, 22.7176, "Закарпатська", "місто", 85000)
        self._add_settlement("Хуст", 48.1761, 23.2994, "Закарпатська", "місто", 29000)
        self._add_settlement("Берегове", 48.2044, 22.6386, "Закарпатська", "місто", 23000)
        self._add_settlement("Виноградів", 48.1400, 23.0386, "Закарпатська", "місто", 25500)
        self._add_settlement("Свалява", 48.5486, 22.9872, "Закарпатська", "місто", 17000)
        self._add_settlement("Рахів", 48.0500, 24.2167, "Закарпатська", "місто", 15600)
        self._add_settlement("Тячів", 48.0117, 23.5722, "Закарпатська", "місто", 9000)
        self._add_settlement("Міжгір'я", 48.5286, 23.5014, "Закарпатська", "селище", 9800)
        self._add_settlement("Великий Березний", 48.8833, 22.4667, "Закарпатська", "селище", 7000)
        
        # Івано-Франківська область
        self._add_settlement("Калуш", 49.0428, 24.3608, "Івано-Франківська", "місто", 65000)
        self._add_settlement("Коломия", 48.5306, 25.0403, "Івано-Франківська", "місто", 61000)
        self._add_settlement("Надвірна", 48.6333, 24.5833, "Івано-Франківська", "місто", 22200)
        self._add_settlement("Яремче", 48.4547, 24.5550, "Івано-Франківська", "місто", 8000)
        self._add_settlement("Бурштин", 49.2586, 24.6347, "Івано-Франківська", "місто", 15400)
        self._add_settlement("Галич", 49.1167, 24.7167, "Івано-Франківська", "місто", 6200)
        self._add_settlement("Рогатин", 49.4167, 24.6167, "Івано-Франківська", "місто", 8100)
        self._add_settlement("Тисмениця", 48.9000, 24.8500, "Івано-Франківська", "місто", 9300)
        
        # Додамо відомі села для прогнозу погоди
        # Села Київської області
        self._add_settlement("Гореничі", 50.5531, 30.3000, "Київська", "село", 3500)
        self._add_settlement("Мотижин", 50.5167, 30.0667, "Київська", "село", 2800)
        self._add_settlement("Крюківщина", 50.3667, 30.3667, "Київська", "село", 4200)
        self._add_settlement("Віта-Поштова", 50.3333, 30.5000, "Київська", "село", 3800)
        self._add_settlement("Софіївська Борщагівка", 50.4167, 30.3667, "Київська", "село", 3200)
        self._add_settlement("Чайки", 50.5833, 30.3333, "Київська", "село", 2500)
        self._add_settlement("Горбовичі", 50.5333, 30.2167, "Київська", "село", 1800)
        self._add_settlement("Демидів", 50.4333, 30.3167, "Київська", "село", 2200)
        
        # Села Львівської області
        self._add_settlement("Рудно", 49.8000, 24.0000, "Львівська", "село", 4500)
        self._add_settlement("Брюховичі", 49.9000, 23.9500, "Львівська", "село", 5200)
        self._add_settlement("Винники", 49.8167, 24.1333, "Львівська", "місто", 18000)
        self._add_settlement("Щирець", 49.6500, 23.8667, "Львівська", "селище", 6500)
        self._add_settlement("Дубляни", 49.8833, 24.0833, "Львівська", "селище", 9800)
        self._add_settlement("Глиняни", 49.8167, 24.5167, "Львівська", "місто", 3200)
        self._add_settlement("Комарно", 49.6333, 23.7000, "Львівська", "місто", 3800)
        self._add_settlement("Миколаїв", 49.5333, 23.9833, "Львівська", "місто", 14800)
        
        # Села Вінницької області
        self._add_settlement("Тиврів", 49.0167, 28.5000, "Вінницька", "селище", 4200)
        self._add_settlement("Стрижавка", 49.3167, 28.4833, "Вінницька", "селище", 3800)
        self._add_settlement("Липовець", 49.2167, 29.0500, "Вінницька", "місто", 8500)
        self._add_settlement("Іллінці", 49.1039, 29.2200, "Вінницька", "місто", 11300)
        self._add_settlement("Літин", 49.3333, 28.0833, "Вінницька", "селище", 6500)
        self._add_settlement("Оратів", 49.1833, 29.5333, "Вінницька", "селище", 3400)
        
        # Села Харківської області
        self._add_settlement("Пісочин", 49.9500, 36.0667, "Харківська", "селище", 8500)
        self._add_settlement("Рогань", 49.9000, 36.4833, "Харківська", "селище", 3200)
        self._add_settlement("Мерефа", 49.8167, 36.0667, "Харківська", "місто", 22100)
        self._add_settlement("Високий", 49.8833, 36.1167, "Харківська", "селище", 12000)
        self._add_settlement("Безлюдівка", 49.8667, 36.2667, "Харківська", "селище", 9500)
        self._add_settlement("Малинівка", 49.8000, 36.7167, "Харківська", "село", 2800)
        
        # Села Одеської області
        self._add_settlement("Затока", 46.0667, 30.4667, "Одеська", "селище", 1800)
        self._add_settlement("Кароліно-Бугаз", 46.1500, 30.5333, "Одеська", "селище", 2200)
        self._add_settlement("Сергіївка", 46.0333, 30.3667, "Одеська", "селище", 2500)
        self._add_settlement("Коблеве", 46.6667, 31.2167, "Одеська", "селище", 1100)
        self._add_settlement("Чорноморськ", 46.3011, 30.6569, "Одеська", "місто", 59000)
        self._add_settlement("Южне", 46.6217, 31.1011, "Одеська", "місто", 32000)
        
        # Села Черкаської області
        self._add_settlement("Сміла", 49.2167, 31.8667, "Черкаська", "місто", 68000)
        self._add_settlement("Умань", 48.7500, 30.2167, "Черкаська", "місто", 82000)
        self._add_settlement("Канів", 49.7500, 31.4667, "Черкаська", "місто", 25000)
        self._add_settlement("Золотоноша", 49.6833, 32.0333, "Черкаська", "місто", 28000)
        self._add_settlement("Ватутіне", 49.0167, 31.0667, "Черкаська", "місто", 17000)
        self._add_settlement("Городище", 49.2906, 31.4514, "Черкаська", "місто", 14200)
        
        # Села Полтавської області
        self._add_settlement("Лубни", 50.0167, 33.0000, "Полтавська", "місто", 45000)
        self._add_settlement("Миргород", 49.9667, 33.6000, "Полтавська", "місто", 39000)
        self._add_settlement("Гадяч", 50.3667, 33.9833, "Полтавська", "місто", 22000)
        self._add_settlement("Горішні Плавні", 49.0094, 33.6450, "Полтавська", "місто", 50000)
        self._add_settlement("Карлівка", 49.4500, 35.1333, "Полтавська", "місто", 15000)
        self._add_settlement("Кобеляки", 49.1500, 34.2167, "Полтавська", "місто", 10000)
        
        # Додамо ще більше сіл для повноти бази
        # Села Волинської області
        self._add_settlement("Ковель", 51.2150, 24.7167, "Волинська", "місто", 69000)
        self._add_settlement("Нововолинськ", 50.7333, 24.1667, "Волинська", "місто", 52000)
        self._add_settlement("Камінь-Каширський", 51.6242, 24.9606, "Волинська", "місто", 10300)
        self._add_settlement("Ківерці", 50.8333, 25.4667, "Волинська", "місто", 13400)
        self._add_settlement("Рожище", 50.9167, 25.2667, "Волинська", "місто", 13100)
        self._add_settlement("Шацьк", 51.4833, 23.9333, "Волинська", "селище", 5300)
        
        # Села Запорізької області
        self._add_settlement("Мелітополь", 46.8489, 35.3653, "Запорізька", "місто", 150000)
        self._add_settlement("Бердянськ", 46.7590, 36.7869, "Запорізька", "місто", 107000)
        self._add_settlement("Токмак", 47.2500, 35.7167, "Запорізька", "місто", 32300)
        self._add_settlement("Оріхів", 47.5678, 35.7853, "Запорізька", "місто", 15400)
        self._add_settlement("Пологі", 47.4764, 36.2531, "Запорізька", "місто", 20000)
        self._add_settlement("Гуляйполе", 47.6633, 36.2614, "Запорізька", "місто", 14700)
        
        # Села Хмельницької області
        self._add_settlement("Кам'янець-Подільський", 48.6806, 26.5806, "Хмельницька", "місто", 98000)
        self._add_settlement("Шепетівка", 50.1833, 27.0667, "Хмельницька", "місто", 40000)
        self._add_settlement("Славута", 50.3000, 26.8667, "Хмельницька", "місто", 34000)
        self._add_settlement("Старокостянтинів", 49.7572, 27.2083, "Хмельницька", "місто", 34000)
        self._add_settlement("Нетішин", 50.3333, 26.6333, "Хмельницька", "місто", 34000)
        self._add_settlement("Волочиськ", 49.5333, 26.2167, "Хмельницька", "місто", 19800)
        
        # Села Тернопільської області
        self._add_settlement("Кременець", 50.1167, 25.7333, "Тернопільська", "місто", 20000)
        self._add_settlement("Чортків", 49.0167, 25.8000, "Тернопільська", "місто", 29000)
        self._add_settlement("Бережани", 49.4500, 24.9333, "Тернопільська", "місто", 17000)
        self._add_settlement("Збараж", 49.6667, 25.7833, "Тернопільська", "місто", 14000)
        self._add_settlement("Заліщики", 48.6500, 25.7333, "Тернопільська", "місто", 9400)
        self._add_settlement("Борщів", 48.8033, 26.0425, "Тернопільська", "місто", 11100)
        
        # Села Рівненської області
        self._add_settlement("Дубно", 50.3939, 25.7592, "Рівненська", "місто", 37000)
        self._add_settlement("Костопіль", 50.8833, 26.4333, "Рівненська", "місто", 31000)
        self._add_settlement("Здолбунів", 50.5167, 26.2500, "Рівненська", "місто", 24000)
        self._add_settlement("Вараш", 51.3333, 25.8500, "Рівненська", "місто", 42000)
        self._add_settlement("Острог", 50.3333, 26.5167, "Рівненська", "місто", 15200)
        self._add_settlement("Сарни", 51.3333, 26.6000, "Рівненська", "місто", 28400)
        
        # Села Сумської області
        self._add_settlement("Конотоп", 51.2369, 33.2027, "Сумська", "місто", 84000)
        self._add_settlement("Шостка", 51.8667, 33.4833, "Сумська", "місто", 73000)
        self._add_settlement("Охтирка", 50.3000, 34.9000, "Сумська", "місто", 47000)
        self._add_settlement("Ромни", 50.7431, 33.4839, "Сумська", "місто", 38000)
        self._add_settlement("Глухів", 51.6781, 33.9167, "Сумська", "місто", 33000)
        self._add_settlement("Білопілля", 51.1500, 34.3000, "Сумська", "місто", 15800)
        
        # Села Чернігівської області
        self._add_settlement("Ніжин", 51.0450, 31.8800, "Чернігівська", "місто", 66000)
        self._add_settlement("Прилуки", 50.5933, 32.3867, "Чернігівська", "місто", 55000)
        self._add_settlement("Новгород-Сіверський", 52.0069, 33.2611, "Чернігівська", "місто", 13000)
        self._add_settlement("Бахмач", 51.1833, 32.8333, "Чернігівська", "місто", 18000)
        self._add_settlement("Городня", 51.8903, 31.5958, "Чернігівська", "місто", 11600)
        self._add_settlement("Корюківка", 51.7833, 32.2500, "Чернігівська", "місто", 13000)
        
        # Села Чернівецької області
        self._add_settlement("Сторожинець", 48.1667, 25.7167, "Чернівецька", "місто", 14000)
        self._add_settlement("Хотин", 48.5078, 26.4922, "Чернівецька", "місто", 9000)
        self._add_settlement("Новодністровськ", 48.5833, 27.4333, "Чернівецька", "місто", 10000)
        self._add_settlement("Кіцмань", 48.4417, 25.7611, "Чернівецька", "місто", 6300)
        self._add_settlement("Вашківці", 48.3833, 25.5167, "Чернівецька", "місто", 5300)
        self._add_settlement("Новоселиця", 48.2167, 26.2667, "Чернівецька", "місто", 7600)
        
        # Села Миколаївської області
        self._add_settlement("Первомайськ", 48.0500, 30.8500, "Миколаївська", "місто", 66000)
        self._add_settlement("Южноукраїнськ", 47.8208, 31.1775, "Миколаївська", "місто", 39000)
        self._add_settlement("Вознесенськ", 47.5667, 31.3333, "Миколаївська", "місто", 34000)
        self._add_settlement("Новий Буг", 47.6833, 32.5167, "Миколаївська", "місто", 15100)
        self._add_settlement("Очаків", 46.6167, 31.5500, "Миколаївська", "місто", 14000)
        self._add_settlement("Снігурівка", 47.0764, 32.8056, "Миколаївська", "місто", 12400)
        
        # Села Херсонської області
        self._add_settlement("Нова Каховка", 46.7500, 33.3667, "Херсонська", "місто", 45000)
        self._add_settlement("Каховка", 46.8000, 33.4667, "Херсонська", "місто", 35000)
        self._add_settlement("Генічеськ", 46.1833, 34.8000, "Херсонська", "місто", 19000)
        self._add_settlement("Скадовськ", 46.1167, 32.9167, "Херсонська", "місто", 18000)
        self._add_settlement("Гола Пристань", 46.5167, 32.5167, "Херсонська", "місто", 14000)
        self._add_settlement("Олешки", 46.6167, 32.7167, "Херсонська", "місто", 24500)
        
        # Додамо популярні курортні села
        self._add_settlement("Пуща-Водиця", 50.5500, 30.3500, "Київська", "місцевість", 3500)
        self._add_settlement("Конча-Заспа", 50.3333, 30.6333, "Київська", "місцевість", 1200)
        self._add_settlement("Ворзель", 50.5500, 30.1500, "Київська", "селище", 6500)
        self._add_settlement("Ірпінь", 50.5167, 30.2500, "Київська", "місто", 60000)
        self._add_settlement("Буча", 50.5500, 30.2167, "Київська", "місто", 36000)
        
        print(f"✅ Завантажено {sum(len(v) for v in self.settlements.values())} записів про населені пункти (міста + села)")
    
    def _add_settlement(self, name: str, lat: float, lon: float, region: str, 
                       settlement_type: str, population: int = 0):
        """Додати населений пункт до бази"""
        if name not in self.settlements:
            self.settlements[name] = []
        
        self.settlements[name].append({
            'lat': lat,
            'lon': lon,
            'region': region,
            'type': settlement_type,
            'population': population
        })
    
    def find_settlements_by_prefix(self, prefix: str, limit: int = 25) -> List[dict]:
        """Знайти населені пункти за першими символами"""
        prefix_lower = prefix.lower()
        results = []
        
        for settlement_name, settlements_list in self.settlements.items():
            if settlement_name.lower().startswith(prefix_lower):
                for settlement in settlements_list:
                    results.append({
                        'name': settlement_name,
                        'full_name': f"{settlement_name} ({settlement['region']})",
                        'region': settlement['region'],
                        'lat': settlement['lat'],
                        'lon': settlement['lon'],
                        'type': settlement['type'],
                        'population': settlement.get('population', 0)
                    })
        
        # Сортуємо за населенням (більші першими), потім за назвою
        results.sort(key=lambda x: (x['population'], x['name']), reverse=True)
        
        return results[:limit]
    
    def find_settlements_by_name(self, name: str, region: str = None) -> List[dict]:
        """Знайти населені пункти за точним іменем"""
        name_lower = name.lower()
        results = []
        
        for settlement_name, settlements_list in self.settlements.items():
            if settlement_name.lower() == name_lower:
                for settlement in settlements_list:
                    if region is None or settlement['region'].lower() == region.lower():
                        results.append({
                            'name': settlement_name,
                            'full_name': f"{settlement_name} ({settlement['region']})",
                            'region': settlement['region'],
                            'lat': settlement['lat'],
                            'lon': settlement['lon'],
                            'type': settlement['type'],
                            'population': settlement.get('population', 0)
                        })
        
        return results
    
    def get_all_regions(self) -> List[str]:
        """Отримати список усіх областей"""
        regions = set()
        for settlements_list in self.settlements.values():
            for settlement in settlements_list:
                regions.add(settlement['region'])
        return sorted(list(regions))
    
    def get_regional_centers(self) -> List[dict]:
        """Отримати список обласних центрів"""
        centers = []
        for name, settlements_list in self.settlements.items():
            for settlement in settlements_list:
                if settlement['type'] in ['обласний центр', 'столиця']:
                    # Перевіряємо, чи вже додали цей центр
                    found = False
                    for center in centers:
                        if center['name'] == name and center['region'] == settlement['region']:
                            found = True
                            break
                    if not found:
                        centers.append({
                            'name': name,
                            'region': settlement['region'],
                            'population': settlement.get('population', 0),
                            'lat': settlement['lat'],
                            'lon': settlement['lon']
                        })
        
        # Сортуємо за алфавітом
        centers.sort(key=lambda x: x['name'])
        return centers
    
    def get_statistics(self) -> dict:
        """Отримати статистику бази даних"""
        total_entries = sum(len(v) for v in self.settlements.values())
        
        regions = {}
        types = {}
        
        for settlements_list in self.settlements.values():
            for settlement in settlements_list:
                region = settlement['region']
                settlement_type = settlement['type']
                
                regions[region] = regions.get(region, 0) + 1
                types[settlement_type] = types.get(settlement_type, 0) + 1
        
        # Найбільші міста
        all_settlements = []
        for name, settlements_list in self.settlements.items():
            for settlement in settlements_list:
                if settlement.get('population', 0) > 0:
                    all_settlements.append({
                        'name': name,
                        'region': settlement['region'],
                        'population': settlement['population'],
                        'type': settlement['type']
                    })
        
        all_settlements.sort(key=lambda x: x['population'], reverse=True)
        largest_cities = all_settlements[:10]
        
        # Дублікати назв
        duplicates = [name for name, lst in self.settlements.items() if len(lst) > 1]
        
        return {
            'unique_names': len(self.settlements),
            'total_entries': total_entries,
            'regions_count': len(regions),
            'regions_distribution': regions,
            'types_distribution': types,
            'largest_cities': largest_cities,
            'duplicates': duplicates,
            'duplicates_count': len(duplicates)
        }
    
    def get_coordinates(self, settlement_name: str, region: str = None) -> Tuple[Optional[float], Optional[float]]:
        """Отримати координати населеного пункту"""
        if settlement_name not in self.settlements:
            return None, None
        
        settlements = self.settlements[settlement_name]
        
        if len(settlements) == 1:
            return settlements[0]['lat'], settlements[0]['lon']
        
        if region:
            for settlement in settlements:
                if settlement['region'].lower() == region.lower():
                    return settlement['lat'], settlement['lon']
        
        return settlements[0]['lat'], settlements[0]['lon']

# Глобальний екземпляр бази даних
settlements_db = UkraineSettlementsDB()