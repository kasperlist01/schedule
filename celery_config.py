import time
from celery import Celery
import main
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

app = Celery('tasks',
             broker='redis://redis:6379/0',
             backend='redis://redis:6379/0')

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 10, 'countdown': 5})
def start_pars(self, faculty):
    try:
        logger.info('Начало выполнения задачи')
        driver = main.setup_driver()
        url = 'https://orel.ranepa.ru/studentam-i-slushatelyam/index.php'
        links = []
        while not links:
            links = main.get_links(faculty.lower(), url, driver)
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
    # 'queue2': {
    #     'exchange': 'queue2',
    #     'routing_key': 'queue2',
    # },
    # 'queue3': {
    #     'exchange': 'queue3',
    #     'routing_key': 'queue3',
    # },
}
