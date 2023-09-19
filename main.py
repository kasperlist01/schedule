import datetime
import json
import locale
import re
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService, Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from parser import write_data


def setup_driver():
    # Настройка веб-драйвера
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
    options = Options()
    options.add_argument("--headless")

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')

    # service = Service("/Users/kasper/Documents/Projecst/IT/Python/rasspisanie/chromedriver")
    service = Service("111/chromedriver")
    # driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_links(url: str) -> dict:
    # Создаем словарь для хранения ссылок и их описаний
    link_dict = {}

    # Создание и настройка веб-драйвера
    driver = setup_driver()

    # try:
    # Открываем страницу в браузере с помощью Selenium
    driver.get(url)
    time.sleep(1)
    print('прошли driver.get(url)')

    # Находим элементы с классом "ranepa-hidden"
    elements = driver.find_elements(By.CLASS_NAME, 'ranepa-hidden')

    # Регулярное выражение для поиска курсов
    pattern = r'[1-4]\s+курс'

    # Выводим текст из каждого найденного элемента, соответствующего регулярному выражению
    for element in elements:
        course = element.find_element(By.CLASS_NAME, 'ranepa-head-line').text
        if re.search(pattern, course):
            ranepa = element.find_element(By.CLASS_NAME, 'ranepa-hidden-content')
            link_elements = ranepa.find_elements(By.TAG_NAME, 'a')
            for link_element in link_elements:
                link = link_element.get_attribute('href')
                description = link_element.get_attribute('text')
                link_dict[description] = link
                # print(f'get_links() {link=}')
    return link_dict


def add_smiley_to_audience_and_teacher(text):
    text = re.sub(r'(\b[ОЧПГ]-\S+\b)', r'\n🏢\1', text)  # Добавляем смайлик перед номером аудитории
    text = re.sub(r'([А-Я][а-я]{1,20}\s[А-Я]\.[А-Я]\.)', r'👨‍🏫\1',
                  text)  # Добавляем смайлик перед именем преподавателя
    return text


def get_timetable(link_dict):
    # Создание и настройка веб-драйвера
    driver = setup_driver()

    # Инициализируем словарь для хранения расписания
    timetable_dict = {}
    subject_list = []
    first = True
    # Создаем словарь с временами для пар
    time_schedule = {
        1: "8.00 – 9.30",
        2: "9.40 – 11.10",
        3: "11.40 – 13.10",
        4: "13.20 – 14.50",
        5: "15.00 – 16.30",
        6: "17.00 – 18.30",
        7: "18.40 – 20.10",
        8: "20.20 – 21.50"
    }

    # Итерируемся по ссылкам и описаниям
    for description, link in link_dict.items():
        driver.get(link)
        time.sleep(1)
        tables = driver.find_elements(By.TAG_NAME, 'table')
        for table in tables:
            for row in table.find_elements(By.TAG_NAME, 'tr')[1:]:
                # Извлекаем ячейки из строки
                cells = row.find_elements(By.TAG_NAME, 'td')
                # Извлекаем информацию из ячеек
                day_of_week = cells[0].text
                if day_of_week != 'Время':
                    for num in range(1, len(cells)):
                        subject = cells[num].text
                        if subject != '' and subject != '_':
                            if first:
                                subject_list.append(
                                    f'📅Расписание на {day_of_week}\n\n🕰{time_schedule[num]}\n📖{subject}')
                                first = False
                            else:
                                subject_list.append(f'🕰{time_schedule[num]}\n📖{subject}')
                                # print(f'get_timetable() {subject_list=}')
                    # Применяем функцию для добавления смайликов
                    subject_list = [add_smiley_to_audience_and_teacher(event) for event in subject_list]
                    # Используем описание и день недели в качестве ключа, а список предметов в качестве значения
                    timetable_dict[description + ' // ' + day_of_week] = subject_list
                    subject_list = []
                    first = True

    if len(timetable_dict) != 0:
        data = write_data()
        today = datetime.datetime.now()
        if 'Файл обновлен' in data.keys():
            date = data['Файл обновлен']
            timetable_dict['Файл обновлен'] = f"{date}\nРасписание обновлено в {today.strftime('%Y-%m-%d %H:%M')}"
        else:
            timetable_dict['Файл обновлен'] = f"Расписание обновлено в {today.strftime('%Y-%m-%d %H:%M')}"

    return timetable_dict


def start_pars():
    url = 'https://orel.ranepa.ru/studentam-i-slushatelyam/index.php'
    while True:
        links = get_links(url)
        print(f'start() {links=}')
        timetable = get_timetable(links)
        print(f'get_timetable() {timetable=}')
        if len(timetable) != 0:
            with open('timetable.json', 'w', encoding='utf-8') as json_file:
                json.dump(timetable, json_file, ensure_ascii=False, indent=4)
            time.sleep(120)
        else:
            time.sleep(5)


if __name__ == "__main__":
    start_pars()
