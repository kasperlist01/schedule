import sqlite3
import locale
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
from tqdm import tqdm
from parser_1 import write_data


def setup_driver():
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
    options = Options()
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.implicitly_wait(7)
    return driver


def get_links(faculty, url: str, driver) -> dict:
    link_dict = {}
    driver.get(url)

    elements = driver.find_elements(By.TAG_NAME, 'h3')

    for element in elements:
        if faculty in element.text.lower():
            # Определение количества следующих элементов для поиска на основе условия
            sibling_count = 4 if faculty in ['колледж', 'аспирантура'] else 2
            
            # Получаем следующие элементы с учетом sibling_count
            next_elements = element.find_elements(By.XPATH, f'./following-sibling::*[contains(@class, "ranepa-hidden")][position() <= {sibling_count}]')
            
            temp_link_dict = {}
            for el in next_elements:
                ranepa = el.find_element(By.CLASS_NAME, 'ranepa-hidden-content')
                link_elements = ranepa.find_elements(By.TAG_NAME, 'a')
                for link_element in link_elements:
                    link = link_element.get_attribute('href')
                    description = link_element.get_attribute('text')
                    temp_link_dict[description] = link
            
            link_dict[element.text] = temp_link_dict

    if len(link_dict) == 1:
        link_dict = list(link_dict.values())[0]
    else:
        for faculty_key, obj in link_dict.items():
            if 'семестр' in faculty_key:
                link_dict = obj
    print('Ссылки получены')

    return link_dict


def add_smiley_to_audience_and_teacher(text):
    text = re.sub(r'(\b[ОЧПГ]-\S+\b)', r'\n🏢\1', text)  # Добавляем смайлик перед номером аудитории
    text = re.sub(r'([А-Я][а-я]{1,20}\s[А-Я]\.[А-Я]\.)', r'👨‍🏫\1',
                  text)  # Добавляем смайлик перед именем преподавателя
    return text

def add_timetable_to_database(timetable_dict, faculty):
    # Подключаемся к базе данных (или создаем новую, если она не существует)
    conn = sqlite3.connect('timetable.db')
    cursor = conn.cursor()
    
    for description_day, subject in timetable_dict.items():
        description, day_of_week = description_day.split(' // ')
        # Проверяем, есть ли уже запись для данной даты, группы и факультета
        cursor.execute("""SELECT ID, Расписание FROM Schedule WHERE
                            Дата=? AND Группа=? AND Факультет=?""", 
                        (day_of_week, description, faculty))
        result = cursor.fetchone()

        if subject:
            if result:
                schedule_id, existing_subject = result
                if existing_subject != subject:
                    # Если предмет изменился, обновляем запись
                    cursor.execute("""UPDATE Schedule SET Расписание=? WHERE ID=?""",
                                    (subject, schedule_id))
            else:
                # Если записи нет, добавляем новую
                cursor.execute("""INSERT INTO Schedule (Дата, Группа, Расписание, Факультет) 
                                    VALUES (?, ?, ?, ?)""", 
                                (day_of_week, description, subject, faculty))
        
    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

def get_timetable(link_dict, driver, faculty):
    # Инициализируем словарь для хранения расписания
    timetable_dict = {}
    subject_list = []
    first = True
    # Создаем словарь с временами для пар
    college_schedule = {
        1: "8.00 – 9.30",
        2: "9.40 – 11.10",
        3: "11.40 – 13.10",
        4: "13.20 – 14.50",
        5: "15.00 – 16.30",
        6: "17.00 – 18.30",
        7: "18.40 – 20.10",
        8: "20.20 – 21.50"
    }

    faculty_schedule = {
        1: "8.00 – 9.20",
        2: "9.40 – 11.00",
        3: "11.30 – 12.50",
        4: "13.10 – 14.30",
        5: "14.50 – 16.10",
        6: "16.40 – 18.00",
        7: "18.20 – 19.40",
        8: "20.00 – 21.20"
    }
    
    time_schedule = faculty_schedule if 'факультет' in faculty.lower() else college_schedule

    for description, link in tqdm(link_dict.items(), desc="Парсинг ссылок", unit="link"):
        driver.get(link)
        tables = driver.find_elements(By.TAG_NAME, 'table')
        for table in tqdm(tables, desc="Обработка таблиц", leave=False):
            for row in table.find_elements(By.TAG_NAME, 'tr')[1:]:
                # Извлекаем ячейки из строки
                cells = row.find_elements(By.TAG_NAME, 'td')
                # Извлекаем информацию из ячеек
                day_of_week = cells[0].text
                if day_of_week != 'Время':
                    day_of_week = day_of_week.replace(',', ', ')
                    for num in range(1, len(cells)):
                        subject = cells[num].text
                        if subject != '' and subject != '_':
                            if first:
                                subject_list.append(
                                    f'📅Расписание на {day_of_week}\n\n🕰{time_schedule[num]}\n📖{subject}')
                                first = False
                            else:
                                subject_list.append(f'🕰{time_schedule[num]}\n📖{subject}')
                    # Применяем функцию для добавления смайликов
                    subject_list = [add_smiley_to_audience_and_teacher(event) for event in subject_list]
                    # Используем описание и день недели в качестве ключа, а список предметов в качестве значения
                    timetable_dict[description + ' // ' + day_of_week] = '\n\n'.join(subject_list)
                    subject_list = []
                    first = True
                

    if timetable_dict:
        add_timetable_to_database(timetable_dict, faculty)

if __name__ == "__main__":
    driver = setup_driver()
    url = 'https://orel.ranepa.ru/studentam-i-slushatelyam/index.php'
    links = []
    while not links:
        links = get_links("Факультет «Государственное и муниципальное управление»".lower(), url, driver)
        time.sleep(5)
    get_timetable(links, driver, "Факультет «Государственное и муниципальное управление»")
