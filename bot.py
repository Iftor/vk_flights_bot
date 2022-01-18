from datetime import datetime
import requests
import vk_api
from pony.orm import db_session
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
import logging
import config
import handlers
from models import UserState, Registration

try:
    import settings
except ImportError:
    settings = None
    exit('Для работы бота требуется токен')


log = logging.getLogger('bot')


def configure_logging():
    """
    Установка параметров логгирования
    """
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)
    
    file_handler = logging.FileHandler('bot.log')
    file_handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)s %(message)s', datefmt='%d-%m-%Y %H:%M'))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)
    
    log.setLevel(logging.DEBUG)


class Bot:
    """
    Сценарий записи на рейс через vk.com
    Use python 3.9
    """
    def __init__(self, _group_id, _token):
        self.group_id = _group_id
        self.token = _token
        self.vk = vk_api.VkApi(token=_token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()
    
    def run(self):
        """
        Запуск бота
        """
        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except:
                log.exception('Ошибка в обработке события')

    @db_session
    def on_event(self, event):
        """
        Обработка события
        :param event: объект события
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info(f'Не умеем обрабатывать события типа {event.type}')
            return
        user_id = event.object.message['peer_id']
        text = event.object.message['text']
        state = UserState.get(user_id=user_id)

        for intent in config.INTENTS:
            if any(token.lower() in text.lower() for token in intent['tokens']):
                log.debug(f'Пользователь получил {intent}')
                # запустить сценарий
                if intent['answer']:
                    if state is not None:
                        state.delete()
                    self.send_text(intent['answer'], user_id)
                else:
                    if state is not None:
                        state.delete()
                    self.start_scenario(user_id, intent['scenario'], text)
                break
        else:
            if state is not None:
                # продолжаем сценарий
                self.continue_scenario(text, state, user_id)
            else:
                self.send_text(config.DEFAULT_ANSWER, user_id)

    def send_text(self, text_to_send, user_id):
        """
        Отправка текста
        :param text_to_send: текст для отправки
        :param user_id: ID пользователя, которому будет отправлен текст
        """
        self.api.messages.send(
            message=text_to_send,
            random_id=get_random_id(),
            peer_id=user_id
        )

    def send_image(self, image, user_id):
        """
        Отправка изображения
        :param image: изображение для отправки
        :param user_id: ID пользователя, которому будет отправлено изображение
        """
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)
        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment = f'photo{owner_id}_{media_id}'

        self.api.messages.send(
            attachment=attachment,
            random_id=get_random_id(),
            peer_id=user_id
        )

    def send_step(self, step, user_id, text, context):
        """
        Отправка сообщения в соответствии с шагом сцинария
        :param step: шаг в сценарии
        :param user_id: ID пользователя, которому будет отправлено сообщение
        :param text: текст сообщения
        :param context: объект контекста
        """
        if 'text' in step:
            self.send_text(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(image, user_id)

    def start_scenario(self, user_id, scenario_name, text):
        """
        Начало сценария
        :param user_id: ID пользователя, с которым начинается диалог
        :param scenario_name: имя сценария
        :param text: текст для отправки
        """
        scenario = config.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_step(step, user_id, text, context={})
        UserState(user_id=user_id, scenario_name=scenario_name, step_name=first_step, context={})

    def continue_scenario(self, text, state, user_id):
        """
        Продолжение сценария
        :param text: текст для отправки
        :param state: объект состояния пользователя внутри сценария
        :param user_id: ID пользователя, с которым ведется диалог
        """
        steps = config.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]
        handler = getattr(handlers, step['handler'])

        handler_result = handler(text=text, context=state.context)
        if handler_result == -1:
            self.send_text(config.DEFAULT_ANSWER, user_id)
            state.delete()
        if handler_result:
            # следующий шаг
            next_step = steps[step['next_step']]
            self.send_step(next_step, user_id, text, state.context)
            if next_step['next_step']:
                # перейти на следующий шаг
                state.step_name = step['next_step']
            else:
                # сцинарий окончен
                log.info('Записался на покупку билетов: {phone_number}'.format(**state.context))
                Registration(
                    phone_number=state.context['phone_number'],
                    departure_city=state.context['departure_city'],
                    destination_city=state.context['destination_city'],
                    date=datetime.strptime(state.context['selected_date'], '%H:%M  %d-%m-%Y'),
                    seats_number=state.context['seats_number'],
                    comment=state.context['comment']
                )
                state.delete()
        else:
            # повтор текущего шага
            text_to_send = step['failure_text'].format(**state.context)
            self.send_text(text_to_send, user_id)


if __name__ == '__main__':
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
