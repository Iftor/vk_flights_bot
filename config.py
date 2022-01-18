
DEFAULT_ANSWER = 'Для записи на рейс введите /ticket'
SEATS_NUMBER = 5
SUGGESTIONS_NUMBER = 5


INTENTS = [
    {
        'name': 'Поиск рейса',
        'tokens': ('/ticket',),
        'scenario': 'flight_search',
        'answer': None,
    },
    {
        'name': 'Помощь',
        'tokens': ('/help',),
        'scenario': None,
        'answer': 'В этом боте вы можете забронировать билет на рейс. Вам понадобится ввести город отправления, город '
                  'назначения и выбрать дату вылета. Также потребуется ввести ваш номер телефона, по которому мы сможем'
                  ' с вами связаться. Для бронирования бидета введите команду /ticket.'
    }
]

SCENARIOS = {
    'flight_search': {
        'first_step': 'step1',
        'steps': {
            'step1': {
                'text': 'Введите город отправления',
                'failure_text': 'Введенный город не найден.\nВыберите город из списка:\n{departure_cities_list_str}',
                'handler': 'handle_departure_city',
                'next_step': 'step2'
            },
            'step2': {
                'text': 'Введите город назначения',
                'failure_text': 'В этот город нет рейса из города {departure_city}.'
                                '\nВыберите город из списка:\n{destination_cities_list_str}',
                'handler': 'handle_destination_city',
                'next_step': 'step3'
            },
            'step3': {
                'text': 'Введите дату в формате 31-01-2021',
                'failure_text': 'Некорректный ввод. Попробуйте еще раз',
                'handler': 'handle_date',
                'next_step': 'step4'
            },
            'step4': {
                'text': 'Выберите номер предпочтительной даты из списка:\n{suggestion_dates_list_str}',
                'failure_text': 'Некорректный ввод.\nВыберите номер даты из списка:\n{suggestion_dates_list_str}',
                'handler': 'handle_choose_flight',
                'next_step': 'step5'
            },
            'step5': {
                'text': 'Введите количество мест от 1 до 5',
                'failure_text': 'Некорректный ввод. Попробуйте еще раз',
                'handler': 'handle_seats_number',
                'next_step': 'step6'
            },
            'step6': {
                'text': 'Напишите комментарий в произвольной форме',
                'failure_text': None,
                'handler': 'handle_comment',
                'next_step': 'step7'
            },
            'step7': {
                'text': 'Город отправления: {departure_city}\n'
                        'Город назначения: {destination_city}\n'
                        'Дата вылета: {selected_date}\n'
                        'Количество мест: {seats_number}\n'
                        'Все верно? Введите "да" или "нет"',
                'failure_text': 'Некорректный ввод. Попробуйте еще раз',
                'handler': 'handle_check',
                'next_step': 'step8'
            },
            'step8': {
                'text': 'Введите ваш номер телефона',
                'failure_text': 'Некоррекнтый номер телефона. Попробуйте еще раз',
                'handler': 'handle_phone_number',
                'next_step': 'step9'
            },
            'step9': {
                'text': 'Спасибо. Мы свяжемся с вами по номеру {phone_number}',
                'image': 'generate_ticket_handler',
                'failure_text': None,
                'handler': None,
                'next_step': None
            }
        }
    }
}
