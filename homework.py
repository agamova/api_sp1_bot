import logging
import os
import requests
import telegram
import time

from dotenv import load_dotenv


load_dotenv()

APPROVED_VERDICT = 'Ревьюеру всё понравилось, работа зачтена!'
BOT_MESSAGE = 'У вас проверили работу "{homework_name}"!\n\n{verdict}'
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
EXCEPT_SLEEP_TIME = 5
EXCEPTION_MESSAGE = 'Бот упал с ошибкой: {error}'
FILEMODE = 'a'
FILENAME = 'main.log'
PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
REJECTED = 'rejected'
REJECTED_VERDICT = 'К сожалению, в работе нашлись ошибки.'
SENDING_MSG = 'Отправлено сообщение.'
SLEEP_TIME = 10 * 60
START_BOT_MSG = 'Бот стартовал!'
START_TIME = 0
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {
    'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
}

logging.basicConfig(level=logging.DEBUG, filename=FILENAME, filemode=FILEMODE)
bot = telegram.Bot(token=TELEGRAM_TOKEN)
logging.debug(START_BOT_MSG)


def parse_homework_status(homework):
    """Returns a message about homework status."""
    homework_status = homework['status']
    homework_name = homework['homework_name']
    if homework_status == REJECTED:
        verdict = REJECTED_VERDICT
    else:
        verdict = APPROVED_VERDICT
    return BOT_MESSAGE.format(homework_name=homework_name, verdict=verdict)


def get_homeworks(current_timestamp):
    """Returns data about all homeworks from current timestamp."""
    url = URL
    headers = HEADERS
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(url, headers=headers, params=params)
    return homework_statuses.json()


def send_message(message):
    """Sends a message to the user with chat_id."""
    return bot.send_message(CHAT_ID, message)


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
                logging.info(SENDING_MSG)
            if homework.get('current_date'):
                current_timestamp = homework['current_date']
            time.sleep(SLEEP_TIME)

        except Exception as e:
            message = EXCEPTION_MESSAGE.format(error=e)
            logging.exception(message)
            send_message(message)
            logging.info(SENDING_MSG)
            time.sleep(EXCEPT_SLEEP_TIME)


if __name__ == '__main__':
    main()
