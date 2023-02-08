import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from telegram.ext import Updater

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

updater = Updater(token=TELEGRAM_TOKEN)

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Прооверят наличие токенов."""
    if PRACTICUM_TOKEN is None:
        logging.critical('PRACTICUM_TOKEN отсутствует')
    if TELEGRAM_TOKEN is None:
        logging.critical('TELEGRAM_TOKEN отсутствует')
    if TELEGRAM_CHAT_ID is None:
        logging.critical('TELEGRAM_CHAT_ID отсутствует')
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot: telegram.Bot, message):
    """Проверяет возможность бота отправить сообщение."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Отправка сообщений работает')
    except Exception as error:
        print(error)
        logging.error('Сообщение не отправляется')


def get_api_answer(timestamp):
    """Проверят Эндпоинт на ответ."""
    try:
        response = requests.get(
            url=ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
        logging.info('Эндпоинт сработал')
        if response.status_code != HTTPStatus.OK:
            logging.error('API не ответил')
            return get_api_answer(timestamp)
    except requests.RequestException as error:
        print(error)
        logging.critical('Эндпоинт недоступен')
    return response.json()


def check_response(response):
    """Проверяет ответ от API."""
    try:
        if type(response) is not dict:
            dict_error = 'Словарь не получен'
            logging.debug(dict_error)
            raise TypeError(dict_error)
        homeworks = response.get('homeworks')
        if type(homeworks) is not list:
            list_error = 'Список домашек не список'
            logging.debug(list_error)
            raise TypeError(list_error)
    except KeyError as error:
        print(error)
        logging.debug('Ключ homeworks отсутствует')
    return homeworks[0]


def parse_status(homework):
    """Получает статус домашки."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if not isinstance(homework, dict):
        raise TypeError('Не словарь')
    if 'homework_name' not in homework:
        raise KeyError('Ключа homework_name не существует')
    if 'status' not in homework:
        raise KeyError('Ключа status не существует')
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError('Такого статуса не существует')

    verdict = HOMEWORK_VERDICTS.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Токены отсутствуют'
        logging.critical(message)
        sys.exit(message)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0

    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        format=FORMAT,
        level=logging.DEBUG,
    )

    while True:
        try:
            api_answer = get_api_answer(timestamp)
            homeworks = check_response(api_answer)
            message = parse_status(homeworks)
            send_message(bot, message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.critical(message)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
