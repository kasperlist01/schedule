import json
import locale
import re
import datetime

user_groups = {}


def load_user_groups():
    try:
        with open('./user_groups.json', 'r', encoding='utf-8') as file:
            user_groups.update(json.load(file))
    except FileNotFoundError:
        pass


# Функция для сохранения данных в файл из user_groups
def save_user_groups():
    with open('./user_groups.json', 'w', encoding='utf-8') as file:
        json.dump(user_groups, file, ensure_ascii=False, indent=4)


def save_messages(data_messages):
    with open('./messages.json', 'w', encoding='utf-8') as file:
        json.dump(data_messages, file, ensure_ascii=False, indent=4)


def write_messages():
    try:
        with open('./messages.json', 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        # Если файл не существует, создаем пустой словарь
        data = {}

    return data


def write_data():
    try:
        with open('./timetable.json', 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        # Если файл не существует, создаем пустой словарь
        data = {}

    return data


def write_users():
    try:
        with open('./user_groups.json', 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        # Если файл не существует, создаем пустой словарь
        data = {}

    return data


def get_grup():
    data = write_data()
    s = set()
    for el in data.keys():
        el = el.split(' // ')[0]
        if not el[0].isnumeric() and el != 'Файл обновлен':
            s.add(el)
    return sorted(list(s))


def select_month(dict):
    month_mapping = {
        'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04',
        'май': '05', 'июн': '06', 'июл': '07', 'авг': '08',
        'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12'
    }

    for month, dates in dict.items():
        ls_new_date = []
        for date in dates:
            new_date = date.replace(date[3:6], month_mapping[date[3:6]])
            ls_new_date.append(new_date)
        dict[month] = ls_new_date
    return dict


def convert_date_format(input_string):
    date_match = re.match(r'^(.*?) // (\d{2})\.(\d{2}) (\w{2})$', input_string)
    if date_match:
        day = date_match.group(2)
        month = date_match.group(3)
        day_name = {
            'Пн': 'Пнд',
            'Вт': 'Втр',
            'Ср': 'Срд',
            'Чт': 'Чтв',
            'Пт': 'Птн',
            'Сб': 'Сбт',
            'Вс': 'Вск'
        }[date_match.group(4)]
        month_name = {
            '01': 'января',
            '02': 'февраля',
            '03': 'марта',
            '04': 'апреля',
            '05': 'мая',
            '06': 'июня',
            '07': 'июля',
            '08': 'августа',
            '09': 'сентября',
            '10': 'октября',
            '11': 'ноября',
            '12': 'декабря'
        }[month]
        new_date = f"{day_name},{day} {month_name}"
        return f"{date_match.group(1)} // {new_date}"
    else:
        return input_string


def format_date_with_day(days_ago):
    day_name = {
        'понедельник': 'Пнд',
        'вторник': 'Втр',
        'среда': 'Срд',
        'четверг': 'Чтв',
        'пятница': 'Птн',
        'суббота': 'Сбт',
        'воскресенье': 'Вск'
    }

    # Устанавливаем русскую локаль
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

    # Получаем текущую дату
    today = datetime.datetime.now()

    # Вычитаем указанное количество дней
    seven_days_ago = today + datetime.timedelta(days=days_ago)

    # Получаем день недели
    day_of_week = day_name[seven_days_ago.strftime('%A').lower()]

    # Форматируем дату с ведущим нулём для дня месяца
    formatted_date = seven_days_ago.strftime('%d %B')

    # Добавляем день недели к отформатированной дате
    formatted_date_with_day = f'{day_of_week},{formatted_date}'

    return formatted_date_with_day


def get_monthly_schedule(group_name):
    # Устанавливаем локаль для правильного разбора даты и времени
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

    # Открываем и читаем JSON-файл с расписанием
    timetable_data = write_data()

    # Извлекаем уникальные даты из расписания
    unique_dates = set(
        group.split(' // ')[1] for group in timetable_data.keys() if group.split(' // ')[0] == group_name)

    # Список месяцев, которые мы будем искать в уникальных датах
    target_months = [
        'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
        'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль'
    ]

    # Фильтруем месяцы, которые есть в уникальных датах
    months_with_schedule = [
        month for month in target_months
        if any(month[:3].upper() == date.split()[1][:3].upper() for date in unique_dates)
    ]

    # Создаем словарь для хранения расписания по месяцам
    monthly_schedule = {month: [] for month in months_with_schedule}

    # Группируем даты по соответствующим месяцам
    for date in unique_dates:
        matching_month = next(
            month for month in months_with_schedule if month[:3].upper() == date.split()[1][:3].upper()
        )
        monthly_schedule[matching_month].append(date)

    # Сортируем даты в каждом месяце и изменяем их формат
    formatted_schedule = {}
    for month, dates in monthly_schedule.items():
        sorted_dates = sorted(dates, key=lambda x: int(x.split(',')[1].split()[0]))
        formatted_dates = [f"{date.split(',')[1].split()[0]}.{date.split()[1][:3]} {date.split(',')[0][:2]}" for date in
                           sorted_dates]
        formatted_schedule[month] = formatted_dates

    return months_with_schedule, select_month(formatted_schedule)


def show_rasp(date):
    data = write_data()
    try:
        msg = '\n\n'.join(data[date]) if len(data[date]) != 0 else 'Нет занятий в этот день🥳'
    except:
        msg = 'Расписание на этот день не заполнено'
    return msg


def add_messages(messages_key, messages_val):
    today = datetime.datetime.now()
    ms_user = write_messages()
    if messages_key in ms_user.keys():
        ms = ms_user[messages_key]
        ms_user[messages_key] = f'{ms}\n{today.strftime("%Y-%m-%d %H:%M")} -- {messages_val}'
    else:
        ms_user[messages_key] = f'{today.strftime("%Y-%m-%d %H:%M")} -- {messages_val}'
    save_messages(ms_user)


def get_messages(messages_key):
    ms_user = write_messages()
    ls_ms_user = ms_user.get(messages_key, '').split('\n')[-30:]
    return '\n'.join(ls_ms_user)


if __name__ == '__main__':
    ls = get_monthly_schedule('Э 303')
    print(ls)
