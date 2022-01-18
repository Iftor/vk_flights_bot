from copy import deepcopy
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch, Mock

from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotEvent
from bot import Bot
import config
from ticket_generation import generate_ticket
from flights import FLIGHTS
from handlers import get_suggestion_dates


def isolate_db(test_func):
    """
    Изолирование базы данных для проведения теста
    :param test_func: функция теста
    """
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()
    return wrapper


class Test1(TestCase):
    RAW_EVENT = {
        'type': 'message_new',
        'object': {
            'message': {
                'date': 1624899179, 'from_id': 81687909, 'id': 77, 'out': 0, 'peer_id': 81687909, 'text': 'А',
                'conversation_message_id': 77, 'fwd_messages': [], 'important': False, 'random_id': 0,
                'attachments': [], 'is_hidden': False
            },
            'client_info': {
                'button_actions': [
                    'text', 'vkpay', 'open_app', 'location', 'open_link', 'callback', 'intent_subscribe',
                    'intent_unsubscribe'
                ],
                'keyboard': True, 'inline_keyboard': True, 'carousel': True, 'lang_id': 0
            }
        },
        'group_id': 202268874,
        'event_id': '253717ff7a6a586a068c5b54519b88baec82f49c'
    }

    def test_run(self):
        count = 5
        obj = {'a': 1}
        events = [obj] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('bot.vk_api.VkApi'):
            with patch('bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.send_image = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count

    INPUTS = [
        'привет',
        '/ticket',
        FLIGHTS[0]['departure_city'],
        FLIGHTS[0]['destination_city'],
        datetime.strftime(datetime.now() + timedelta(days=50), '%d-%m-%Y'),
        '3',
        '7',
        '1',
        'Нужны билеты в первый класс',
        'да',
        '89037463761',
    ]

    SUGGESTION_DATES = get_suggestion_dates(INPUTS[2], INPUTS[3], datetime.strptime(INPUTS[4], '%d-%m-%Y'))

    EXPECTED_OUTPUTS = [
        config.DEFAULT_ANSWER,
        config.SCENARIOS['flight_search']['steps']['step1']['text'],
        config.SCENARIOS['flight_search']['steps']['step2']['text'],
        config.SCENARIOS['flight_search']['steps']['step3']['text'],
        config.SCENARIOS['flight_search']['steps']['step4']['text'].format(
            suggestion_dates_list_str='\n'.join(
                [f"{i + 1}. {datetime.strftime(date, '%H:%M  %d-%m-%Y')}" for i, date in enumerate(SUGGESTION_DATES)]
            )
        ),
        config.SCENARIOS['flight_search']['steps']['step5']['text'],
        config.SCENARIOS['flight_search']['steps']['step5']['failure_text'],
        config.SCENARIOS['flight_search']['steps']['step6']['text'],
        config.SCENARIOS['flight_search']['steps']['step7']['text'].format(
            departure_city=INPUTS[2],
            destination_city=INPUTS[3],
            selected_date=datetime.strftime(SUGGESTION_DATES[2], '%H:%M  %d-%m-%Y'),
            seats_number='1'
        ),
        config.SCENARIOS['flight_search']['steps']['step8']['text'],
        config.SCENARIOS['flight_search']['steps']['step9']['text'].format(phone_number='89037463761'),
    ]

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)
        with patch('bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot('', '')
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()

        assert send_mock.call_count == len(self.INPUTS)
        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])
        assert real_outputs == self.EXPECTED_OUTPUTS

    def test_ticket_generation(self):
        with open('./files/test_avatar.svg', 'rb') as avatar_file:
            avatar_mock = Mock()
            avatar_mock.content = avatar_file.read()
        with patch('requests.get', return_value=avatar_mock):
            ticket_file = generate_ticket('Москва', 'Петербург', '10-12-2021', '89375647385')
        with open('./files/ticket_example.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()
        assert ticket_file.read() == expected_bytes
