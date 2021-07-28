import logging
import os
import requests
import telegram
import time

from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler


load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

bot = telegram.Bot(token=TELEGRAM_TOKEN)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename='main.log',
    filemode='w'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'my_logger.log',
    maxBytes=50000000,
    backupCount=5
)
logger.addHandler(handler)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None or homework_status is None:
        raise Exception('Homework not found')
    statuses = {
        'reviewing': 'Работа взята в ревью',
        'rejected': 'К сожалению, в работе нашлись ошибки.',
        'approved': 'Ревьюеру всё понравилось, работа зачтена!'
    }
    verdict = statuses[homework_status]
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    try:
        headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
        payload = {'from_date': current_timestamp}
        homework_statuses = requests.get(
            url=URL,
            headers=headers,
            params=payload
        )
        return homework_statuses.json()
    except Exception as e:
        logger.exception(f'Error: {e}')
        send_message(f'Error: {e}')


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    logger.debug('Бот запущен!')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homeworks(current_timestamp)
            result = new_homework.get('homeworks')
            if result:
                send_message(
                    parse_homework_status(result[0])
                )
                logger.info('Сообщение отправлено')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            time.sleep(5 * 60)  # Опрашивать раз в пять минут

        except Exception as e:
            logger.error(f'Бот упал с ошибкой: {e}')
            send_message(f'Бот упал с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
