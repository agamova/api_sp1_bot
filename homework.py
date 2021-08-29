import logging
import os
import requests
import telegram
import time

from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from telegram import TelegramError


load_dotenv()


BOT_ERROR_MSG = 'Ошибка инициализации бота: {error}'
MSG_BOT_IS_DOWN = 'Бот упал с ошибкой: {error}'
MSG_VAR_NOT_FOUND = ('Не найдена переменная {var} в пространстве'
                     ' переменных среды')
FILENAME = __file__ + '.log'
HOMEWORK_ERROR_MSG = ('Отсутствует необходимая информация о домашней работе.\n'
                      'status: {status}, name: {name}')
LOG_FORMAT = '%(asctime)s, %(levelname)s, %(message)s, %(name)s'
REQUEST_ERR_MSG = 'Не удалось выполнить запрос {dict}! Ошибка {error}.'
JSON_ERROR_MSG = 'Запрос выполнен с ошибкой: {error}, код: {code}'
SENDING_MSG = 'Отправлено сообщение.'
SEND_MESSAGE_ERROR = 'Ошибка при отправке сообщения!'
SLEEP_TIME = 10 * 60
START_BOT_MSG = 'Бот стартовал!'
START_TIME = int(time.time())
TIME_ERROR_MSG = '{timestamp} не конвертируется в дату!'
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
try:
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
except KeyError as error:
    raise KeyError(MSG_VAR_NOT_FOUND.format(var=error))
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
STATUSES_DICT = {
    'rejected': ('У вас проверили работу "{homework_name}"!\n\n'
                 'К сожалению, в работе нашлись ошибки.'),
    'approved': ('У вас проверили работу "{homework_name}"!\n\n'
                 'Ревьюеру всё понравилось, работа зачтена!'),
    'reviewing': 'Работа {homework_name} взята в ревью.',
}

logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(FILENAME, maxBytes=50000000, backupCount=2)
logger.addHandler(handler)
bot = telegram.Bot(token=TELEGRAM_TOKEN)
# try:
#     bot.get_me()
#     logger.debug(START_BOT_MSG)
# except TelegramError as error:
#     raise TelegramError(BOT_ERROR_MSG.format(error=error))


def parse_homework_status(homework):
    """Returns a message about homework status."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_status not in STATUSES_DICT or not homework_name:
        raise KeyError(
            HOMEWORK_ERROR_MSG.format(
                status=homework_status,
                name=homework_name
            )
        )
    verdict = STATUSES_DICT.get(homework_status)
    return verdict.format(homework_name=homework_name)


def get_homeworks(current_timestamp):
    """Returns data about all homeworks from current timestamp."""
    try:
        time.ctime(current_timestamp)
    except TypeError:
        raise TypeError(TIME_ERROR_MSG.format(timestamp=current_timestamp))
    params = {'from_date': current_timestamp}
    request_dict = {'url': URL, 'headers': HEADERS, 'params': params}
    try:
        response = requests.get(**request_dict)
        response_dict = response.json()
        if response_dict.get('code') or response_dict.get('error'):
            code = response_dict.get('code')
            error = response_dict.get('error')
            raise Exception(JSON_ERROR_MSG.format(error=error, code=code))
        return response_dict
    except Exception as error:
        raise Exception(REQUEST_ERR_MSG.format(error=error, dict=request_dict))


def send_message(message):
    """Sends a message to the user with chat_id."""
    if message:
        try:
            bot.send_message(CHAT_ID, message)
            logger.info(SENDING_MSG)
        except Exception as error:
            raise Exception(error)


def main():
    """Bot sends messages about homework status."""
    current_timestamp = START_TIME
    while True:
        try:
            homework = get_homeworks(current_timestamp)
            if homework.get('homeworks'):
                last_homework = homework['homeworks'][0]
                message = parse_homework_status(last_homework)
                send_message(message)
            if homework.get('current_date'):
                current_timestamp = homework['current_date']
            time.sleep(SLEEP_TIME)
        except Exception as error:
            message = MSG_BOT_IS_DOWN.format(error=error)
            logger.exception(message)
            send_message(message)
            raise Exception(error)


if __name__ == '__main__':
    main()
