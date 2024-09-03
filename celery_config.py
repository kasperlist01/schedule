import time
from celery import Celery
import main
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

app = Celery('tasks',
             broker='redis://redis:6379/0',
             backend='redis://redis:6379/0')

urls = {
    "Юридический факультет": "https://orel.ranepa.ru/raspisanie/yuridicheskiy-fakultet/",
    "Факультет «Экономика и менеджмент»": "https://orel.ranepa.ru/raspisanie/ekonomicheskiy-fakultet/",
    "Факультет технологий, товароведения и сервиса": "https://orel.ranepa.ru/raspisanie/tekhnologicheskiy-fakultet/",
    "Факультет «Государственное и муниципальное управление»": "https://orel.ranepa.ru/raspisanie/raspisanie-gosudarstvennoe-i-munitsipalnoe-upravlenie/",
    "Колледж": "https://orel.ranepa.ru/raspisanie/kolledzh/"
}

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 10, 'countdown': 5})
def start_pars(self, faculty):
    try:
        logger.info('Начало выполнения задачи')
        driver = main.setup_driver()
        links = []
        while not links:
            links = main.get_links(urls[faculty], driver)
            time.sleep(5)
        main.get_timetable(links, driver, faculty)
        logger.info('Процесс завершен')
    except Exception as e:
        logger.error(f'Ошибка при выполнении задачи: {e}', exc_info=True)
        raise


app.conf.task_queues = {
    'queue1': {
        'exchange': 'queue1',
        'routing_key': 'queue1',
    },
}
