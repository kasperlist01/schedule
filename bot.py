import asyncio
import datetime
import re
from aiogram import Bot, Dispatcher
from aiogram import types, F
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from database import Database
from aiogram.enums import ParseMode
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
import psutil

from config import token

bot = Bot(token=token, parse_mode=ParseMode.HTML)
db = Database()
dp = Dispatcher()


class MyCallback(CallbackData, prefix="pref"):
    action: str
    val: str


@dp.message(CommandStart())
async def start(message: types.Message):
    faculties = {
        '📚 Юридический': 'Юридический',
        '💼 Экономика и менеджмент': 'менеджмент',
        '🔧 Технологий, товароведения и сервиса': 'товароведения',
        '🏛 Государственное и муниципальное управление': 'муниципальное',
        '🎓 Колледж': 'Колледж',
        # '👨‍🎓 Аспирантура': 'Аспирантура'
    }
    builder = InlineKeyboardBuilder()
    for faculty_name, faculty_id in faculties.items():
        builder.button(text=faculty_name, callback_data=MyCallback(action='faculty', val=faculty_id))
    builder.adjust(2)
    await message.answer(f'🎓 Выберите факультет:', reply_markup=builder.as_markup())


@dp.callback_query(MyCallback.filter(F.action == "faculty"))
async def choose_course(callback: types.CallbackQuery, callback_data: MyCallback):
    faculty = callback_data.val
    groups = db.get_groups_by_faculty(faculty)
    max_course = sorted([int(re.search(r'\d', course).group()) for course in groups])[-1]
    builder = InlineKeyboardBuilder()
    builder2 = InlineKeyboardBuilder()
    for course in range(1, max_course + 1):
        builder.button(text=f"{course} курс", callback_data=MyCallback(action='course', val=f'{faculty}//{course}'))
    builder.adjust(2)
    builder2.button(text="⬅ Назад", callback_data=MyCallback(action='go_back_to_start', val='start'))
    builder2.adjust(1)
    builder.attach(builder2)
    await callback.message.edit_text(f'📚 Выберите курс на факультете:', reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(MyCallback.filter(F.action == "course"))
async def choose_group(callback: types.CallbackQuery, callback_data: MyCallback):
    faculty = callback_data.val.split('//')[0]
    course = int(callback_data.val.split('//')[1])
    groups = db.get_groups_by_faculty(faculty)
    filtered_groups = [group for group in groups if int(re.search(r'\d', group).group()) == course]
    builder = InlineKeyboardBuilder()
    builder2 = InlineKeyboardBuilder()
    for group in filtered_groups:
        builder.button(text=group, callback_data=MyCallback(action='group', val=f'{faculty}//{course}//{group}').pack())

    if len(filtered_groups) <= 6:
        rows = 2  # Для небольшого количества кнопок делаем 2 ряда
    elif len(filtered_groups) <= 12:
        rows = 3  # Для среднего количества кнопок используем 3 ряда
    else:
        rows = 4  # Для большего количества кнопок используем 4 ряда или более

    builder.adjust(rows)
    builder2.button(text="⬅ Назад", callback_data=MyCallback(action='faculty', val=faculty))
    builder2.adjust(1)
    builder.attach(builder2)
    await callback.message.edit_text('📚 Выберите группу:', reply_markup=builder.as_markup())
    await callback.answer()


@dp.callback_query(MyCallback.filter(F.action == "group"))
async def show_schedule_options(callback: types.CallbackQuery, callback_data: MyCallback):
    faculty, course, group = callback_data.val.split('//')[0], callback_data.val.split('//')[1], \
    callback_data.val.split('//')[2]

    confirmation_message = (
        f"*Вы выбрали:*\n"
        f"🎓 *Факультет:* {faculty}\n"
        f"📚 *Курс:* {course}\n"
        f"👥 *Группа:* {group}\n\n")

    db.add_or_update_user(name=callback.message.chat.first_name, group=group, channel_id=callback.message.chat.id)
    kb_bt = [
        [types.KeyboardButton(text="Расписание на сегодня"), types.KeyboardButton(text="Расписание на завтра")],
        [types.KeyboardButton(text="Выбрать дату")]
    ]
    if callback.message.chat.id in [851960898, 1074252469]:
        kb_bt[1].append(types.KeyboardButton(text="Сервисное меню"))
    builder = types.ReplyKeyboardMarkup(keyboard=kb_bt, resize_keyboard=True)

    await callback.message.answer(confirmation_message, reply_markup=builder, parse_mode="Markdown")
    await callback.answer()


@dp.message(F.text.lower() == "расписание на сегодня")
async def show_schedule_today(message: types.Message):
    group = db.get_group_by_channel_id(message.chat.id)
    date = datetime.date.today()
    schedule = db.get_schedule_by_date(group=group, target_date=date)
    await message.answer(schedule)


@dp.message(F.text.lower() == "расписание на завтра")
async def show_schedule_tomorrow(message: types.Message):
    group = db.get_group_by_channel_id(message.chat.id)
    date = datetime.date.today() + datetime.timedelta(days=1)
    schedule = db.get_schedule_by_date(group=group, target_date=date)
    await message.answer(schedule)


@dp.message(F.text.lower() == "выбрать дату")
async def show_calendar(message: types.Message):
    await message.answer('Выберите дату',
                         reply_markup=await SimpleCalendar(locale='ru_RU.UTF-8').start_calendar()
                         )


@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: CallbackData):
    calendar = SimpleCalendar(
        locale='ru_RU.UTF-8', show_alerts=True
    )
    calendar.set_dates_range(datetime.datetime(2020, 1, 1), datetime.datetime(2030, 12, 31))
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        group = db.get_group_by_channel_id(callback_query.message.chat.id)
        schedule = db.get_schedule_by_date(group=group, target_date=date)
        await callback_query.message.delete()
        await callback_query.message.answer(schedule)


@dp.callback_query(MyCallback.filter(F.action == "go_back_to_start"))
async def go_back_to_start(callback_query: types.CallbackQuery, callback_data: MyCallback):
    await callback_query.message.delete()
    await start(callback_query.message)


@dp.message(F.text.lower() == "сервисное меню")
async def def_menu(message: types.Message):
    if message.chat.id in [851960898, 1074252469]:
        builder = InlineKeyboardBuilder()
        for group_action in ['База расписания', 'Список пользователей', 'Температура сервера', 'История сообщений']:
            builder.button(text=group_action, callback_data=MyCallback(action='def_menu', val=group_action))
        builder.adjust(2)
        await message.answer(f'Меню администратора', reply_markup=builder.as_markup())
    else:
        await message.answer('У вас нет прав на использование этой команды')


@dp.callback_query(MyCallback.filter(F.action == "def_menu"))
async def ch_rasp_date(callback: types.CallbackQuery, callback_data: MyCallback):
    response = ''
    if callback_data.val == 'База расписания':
        response = "<b>Время последних обновлений расписаний по факультетам:</b>\n\n"
        faculties = {
            '📚 Юридический': 'Юридический',
            '💼 Экономика и менеджмент': 'менеджмент',
            '🔧 Технологий, товароведения и сервиса': 'товароведения',
            '🏛 Государственное и муниципальное управление': 'муниципальное',
            '🎓 Колледж': 'Колледж',
            # '👨‍🎓 Аспирантура': 'Аспирантура'
        }
        for faculty_key, faculty_val in faculties.items():
            times = db.fetch_check_dates(faculty_val)
            if times:
                times_str = times
                response += f"<i>{faculty_key}:</i> {times_str}\n"
            else:
                response += f"<i>{faculty_key}:</i> Нет данных\n"
        await callback.message.answer(response, parse_mode='HTML')
        await def_menu(callback.message)
    elif callback_data.val == 'Список пользователей':
        data_user = db.get_list_users()
        user_parts = [f'{num}. {el}' for num, el in enumerate(data_user, 1)]
        full_message = f'Пользователей в базе - {len(data_user)} человек\n\n' + '\n'.join(user_parts)

        if len(full_message) > 4096:
            parts = []
            part = ''
            header = f'Пользователей в базе - {len(data_user)} человек\n\n'
            for user_part in user_parts:
                if len(part + user_part + '\n') < 4096 - len(header):
                    part += user_part + '\n'
                else:
                    if not parts:
                        part = header + part
                    parts.append(part.strip())
                    part = user_part + '\n'
            if part:
                if not parts:
                    part = header + part
                parts.append(part.strip())
        else:
            parts = [full_message]

        for part in parts:
            await callback.message.answer(part)

        await def_menu(callback.message)

    elif callback_data.val == 'Температура сервера':
        try:
            temperature_info = psutil.sensors_temperatures(fahrenheit=False)
            if "coretemp" in temperature_info:
                core_temp = temperature_info["coretemp"]
                # Отсортируем по номеру ядра
                core_temp = sorted(core_temp,
                                   key=lambda x: int(x.label.split(' ')[1]) if x.label.startswith('Core') else float(
                                       'inf'))
                response = ""
                for entry in core_temp:
                    response += f"Температура {entry.label}: {entry.current}°C\n"
            else:
                response = "Информация о температуре не доступна."
        except AttributeError:
            response = "Модуль psutil не поддерживает получение информации о температуре."
        await callback.message.answer(response)
        await def_menu(callback.message)
    # elif callback_data.val == 'История сообщений':
    #     data_user = write_users()
    #     ls_users = [ky for ky in data_user.keys()]
    #     builder = InlineKeyboardBuilder()
    #     for group_action in ls_users:
    #         builder.button(text=group_action, callback_data=MyCallback(action='ch_user', val=group_action))
    #     builder.adjust(2)
    #     await callback.message.answer(f'Выберите пользователя', reply_markup=builder.as_markup())
    # if callback_data.val != 'История сообщений':
    #     await callback.message.answer(response)
    #     await def_menu(callback.message)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
