import re
from datetime import datetime, timedelta

from config import SUGGESTIONS_NUMBER, SEATS_NUMBER
from ticket_generation import generate_ticket
from flights import FLIGHTS


def check_on_vowel(letter):
    """
    Проверка буквы на гласность
    :param letter: проверяемая буква
    :return: гласность буквы
    """
    vowels = ['а', 'у', 'о', 'ы', 'и', 'э', 'я', 'ю', 'ё', 'е']
    return letter in vowels


def get_suggestion_dates(input_departure_city, input_destination_city, input_date):
    """
    Получание дат рейсов из города отправления в город назначения
    :param input_departure_city: выбранный город отправления
    :param input_destination_city: выбранный город назначения
    :param input_date:  выбранная дата рейса
    :return: даты рейсов
    """
    valid_suggestions = []    # предложения с соответствием городов отправления и назначения
    for flight in FLIGHTS:
        if flight['departure_city'] == input_departure_city:
            if flight['destination_city'] == input_destination_city:
                if flight['departure_date']['date'] > datetime.now():
                    valid_suggestions.append(flight)

    period_suggestions = []    # переодические даты
    valid_suggestions = sorted(valid_suggestions,
                               key=lambda x: abs(x['departure_date']['date'] - input_date))
    for suggestion in valid_suggestions:    # поиск ближайших переодических дат для каждой переодической
        departure_date = suggestion['departure_date']
        date = departure_date['date']
        period = departure_date['period']
        if period:    # если есть период
            if input_date < date:
                fact = -1
            else:
                fact = 1
            nearest_date_suggestion = date + timedelta(**{period: fact})    # близжайшая дата
            i = 2
            while True:
                period_date_suggestion = date + timedelta(**{period: fact * i})
                if abs(input_date - period_date_suggestion) < abs(
                        input_date - nearest_date_suggestion):
                    nearest_date_suggestion = period_date_suggestion
                else:
                    i -= 1
                    break
                i += 1
            for j in range(SUGGESTIONS_NUMBER):    # добавление нескольких дат близких к ближайшей
                period_date_suggestion = nearest_date_suggestion + timedelta(**{period: fact * j})
                comparing_index = SUGGESTIONS_NUMBER - 1 \
                    if len(valid_suggestions) >= SUGGESTIONS_NUMBER else len(valid_suggestions) - 1
                if abs(input_date - period_date_suggestion) < abs(
                        input_date - valid_suggestions[comparing_index]['departure_date']['date']
                ):
                    period_suggestions.append(period_date_suggestion)
                else:
                    break
    suggestion_dates = [suggestion['departure_date']['date'] for suggestion in valid_suggestions]    # без учета
                                                                                                     #  периодических
    suggestion_dates = sorted(suggestion_dates + period_suggestions,
                              key=lambda x: abs(x - input_date))[:SUGGESTIONS_NUMBER]
    # с учетом переодических
    # все отсортировано по разнице с датой введенной пользователем
    # взяты только первые несколько

    return sorted(suggestion_dates)


def handle_departure_city(text, context):
    """
    Обработчик города отправления
    :param text: введенный пользователем текст
    :param context: объект контекста
    """
    text = text.capitalize()
    departure_cities_list = {flight['departure_city'] for flight in FLIGHTS}
    for city in departure_cities_list:
        if re.search(f'{city[:-1] if check_on_vowel(city[-1]) else city}[а-я]*', text):
            context['departure_city'] = city
            return True
    else:
        if 'departure_cities_list_str' not in context:
            context['departure_cities_list_str'] = '\n'.join(map(lambda x: f'- {x}', departure_cities_list))
        return False


def handle_destination_city(text, context):
    """
    Обработчик города назначения
    :param text: введенный пользователем текст
    :param context: объект контекста
    """
    text = text.capitalize()
    destination_cities_list = {
        flight['destination_city'] for flight in FLIGHTS if flight['departure_city'] == context['departure_city']
    }
    for city in destination_cities_list:
        if re.search(f'{city[:-1] if check_on_vowel(city[-1]) else city}[а-я]*', text):
            context['destination_city'] = city
            return True
    else:
        if 'destination_cities_list_str' not in context:
            context['destination_cities_list_str'] = '\n'.join(map(lambda x: f'- {x}', destination_cities_list))
        return False


def handle_date(text, context):
    """
    Обработчик даты
    :param text: введенный пользователем текст
    :param context: объект контекста
    """
    try:
        if datetime.strptime(text, '%d-%m-%Y') > datetime.now():
            context['departure_date'] = text
            suggestion_dates = get_suggestion_dates(context['departure_city'], context['destination_city'],
                                                    datetime.strptime(text, '%d-%m-%Y'))
            context['suggestion_dates_list'] = list(map(
                lambda date: datetime.strftime(date, '%H:%M  %d-%m-%Y'),
                suggestion_dates
            ))
            context['suggestion_dates_list_str'] = '\n'.join(
                [f"{i + 1}. {datetime.strftime(date, '%H:%M  %d-%m-%Y')}" for i, date in enumerate(suggestion_dates)]
            )
            return True
        else:
            return False
    except:
        return False


def handle_choose_flight(text, context):
    """
    Обработчик выбора рейса
    :param text: введенный пользователем текст
    :param context: объект контекста
    """
    try:
        choice = int(text) - 1
        if choice not in range(len(context['suggestion_dates_list'])):
            raise ValueError
        context['selected_date'] = context['suggestion_dates_list'][choice]
        return True
    except:
        return False


def handle_seats_number(text, context):
    """
    Обработчик количества мест
    :param text: введенный пользователем текст
    :param context: объект контекста
    """
    try:
        if int(text) - 1 in range(SEATS_NUMBER):
            context['seats_number'] = int(text)
            return True
        else:
            return False
    except:
        return False


def handle_comment(text, context):
    """
    Обработчик комментария
    :param text: введенный пользователем текст
    :param context: объект контекста
    """
    if text:
        context['comment'] = text
    else:
        context['comment'] = None
    return True


def handle_check(text, context):
    """
    Обработчик подтверждения пользователем правильности данных
    :param text: введенный пользователем текст
    :param context: объект контекста
    """
    if text.lower() == 'да':
        return True
    elif text.lower() == 'нет':
        return -1   # знак выхода из сценария
    else:
        return False


def handle_phone_number(text, context):
    """
    Обработчик номера телефона
    :param text: введенный пользователем текст
    :param context: объект контекста
    """
    match_phone_number = re.match(r'^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$', text)
    if match_phone_number:
        context['phone_number'] = match_phone_number[0]
        return True
    else:
        return False


def generate_ticket_handler(text, context):
    """
    Генерация билета
    :param text: введенный пользователем текст (отсутствует)
    :param context: объект контекста
    """
    return generate_ticket(dep_city=context['departure_city'], des_city=context['destination_city'],
                           date=context['selected_date'], phone_number=context['phone_number'])
