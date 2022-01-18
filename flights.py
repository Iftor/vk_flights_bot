from datetime import datetime
from random import randint, choice
import time


POSSIBLE_DEPARTURE_CITIES = ['Москва', 'Екатеринбург', 'Лондон', 'Париж', 'Рига', 'Киев', 'Минск', 'Иваново']
POSSIBLE_DESTINATION_CITIES = ['Москва', 'Брянск', 'Краснодар', 'Лондон', 'Иркутск', 'Киев', 'Липецк', 'Иваново']


def get_random_date():
    """
    Получение случайной даты
    """
    date_seconds = time.time() + randint(0, 8000000)
    return {'date': datetime.fromtimestamp(date_seconds), 'period': None}


def get_random_periodic_date():
    """
    Получение случайной переодической даты
    """
    date_seconds = time.time() + randint(0, 604800)
    return {'date': datetime.fromtimestamp(date_seconds), 'period': 'weeks'}


FLIGHTS = []

departure_city = choice(POSSIBLE_DEPARTURE_CITIES)
destination_city = choice([city for city in POSSIBLE_DESTINATION_CITIES if city != departure_city])
departure_date = get_random_periodic_date()
FLIGHTS.append({
    'departure_city': departure_city,
    'destination_city': destination_city,
    'departure_date': departure_date
})

for _ in range(500):
    departure_city = choice(POSSIBLE_DEPARTURE_CITIES)
    destination_city = choice([city for city in POSSIBLE_DESTINATION_CITIES if city != departure_city])
    departure_date = choice([get_random_date, get_random_periodic_date])()
    FLIGHTS.append({
        'departure_city': departure_city,
        'destination_city': destination_city,
        'departure_date': departure_date
    })
