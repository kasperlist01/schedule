import asyncio
from aiogram import Bot, Dispatcher
from aiogram import types, F
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
import psutil

from config import token
from parser import get_grup, get_monthly_schedule, convert_date_format, show_rasp, format_date_with_day, \
    load_user_groups, user_groups, save_user_groups, write_data, write_users

bot = Bot(token=token)

dp = Dispatcher()
user = {}
month = []


class MyCallback(CallbackData, prefix="pref"):
    action: str
    val: str


@dp.message(CommandStart())
async def start(message: types.Message):
    load_user_groups()
    groups = get_grup()
    builder = InlineKeyboardBuilder()
    for group_action in groups:
        builder.button(text=group_action, callback_data=MyCallback(action='group', val=group_action))
    builder.adjust(4)
    await message.answer(f'Выберите группу', reply_markup=builder.as_markup())


@dp.callback_query(MyCallback.filter(F.action == "group"))
async def ch_rasp_date(callback: types.CallbackQuery, callback_data: MyCallback):
    user_name = f'{callback.message.chat.first_name}_{callback.message.chat.id}'
    selected_group = callback_data.val
    user_groups[user_name] = selected_group  # Обновляем словарь
    save_user_groups()
    kb = [
        [types.KeyboardButton(text="Расписание на сегодня"), types.KeyboardButton(text="Расписание на завтра")],
        [types.KeyboardButton(text="Выбрать дату")]
    ]
    builder = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await callback.message.delete()
    await callback.message.answer(
        f"Выбрана группа - {user_groups[f'{callback.message.chat.first_name}_{callback.message.chat.id}']}",
        reply_markup=builder)


@dp.message(F.text.lower() == "расписание на сегодня")
async def ch_month(message: types.Message):
    load_user_groups()
    user_name = f'{message.chat.first_name}_{message.chat.id}'
    group_schedule = user_groups[user_name]
    date = convert_date_format(f'{group_schedule} // {format_date_with_day(0)}')
    rasp = show_rasp(date)
    await message.answer(rasp)


@dp.message(F.text.lower() == "расписание на завтра")
async def ch_month(message: types.Message):
    load_user_groups()
    user_name = f'{message.chat.first_name}_{message.chat.id}'
    group_schedule = user_groups[user_name]
    date = convert_date_format(f'{group_schedule} // {format_date_with_day(1)}')
    rasp = show_rasp(date)
    await message.answer(rasp)


@dp.message(F.text.lower() == "выбрать дату")
async def ch_month(message: types.Message):
    load_user_groups()
    global month
    user_name = f'{message.chat.first_name}_{message.chat.id}'
    month, _ = get_monthly_schedule(user_groups[user_name])
    kb = []
    row = []
    for action in month:
        if len(row) == 3:
            kb.append(row)
            row = []
        row.append(types.KeyboardButton(text=action, callback_data=MyCallback(action='month', val=action)))
    if row:
        kb.append(row)
    builder = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Выберите месяц", reply_markup=builder)


def is_month(message: types.Message):
    text = str(message.text)
    return text in month


@dp.message(is_month)
async def ch_day(message: types.Message):
    load_user_groups()
    user_name = f'{message.chat.first_name}_{message.chat.id}'
    _, date = get_monthly_schedule(user_groups[user_name])
    builder = InlineKeyboardBuilder()
    date = date[message.text]
    for action in date:
        builder.button(text=action, callback_data=MyCallback(action='day', val=action))
    builder.adjust(3)
    await message.answer(message.text, reply_markup=builder.as_markup())


@dp.callback_query(MyCallback.filter(F.action == "day"))
async def show_rasp_tel(callback: types.CallbackQuery, callback_data: MyCallback):
    load_user_groups()
    group = user_groups[f'{callback.message.chat.first_name}_{callback.message.chat.id}']
    date = convert_date_format(group + ' // ' + callback_data.val)
    rasp = show_rasp(date)
    kb = [
        [types.KeyboardButton(text="Расписание на сегодня"), types.KeyboardButton(text="Расписание на завтра")],
        [types.KeyboardButton(text="Выбрать дату")]
    ]
    builder = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await callback.message.delete()
    await callback.message.answer(rasp, reply_markup=builder)


@dp.message(F.text.lower() == "сервисное меню")
async def def_menu(message: types.Message):
    if message.chat.id in [851960898, 1074252469]:
        builder = InlineKeyboardBuilder()
        for group_action in ['База расписания', 'Список пользователей', 'Температура сервера']:
            builder.button(text=group_action, callback_data=MyCallback(action='def_menu', val=group_action))
        builder.adjust(2)
        await message.answer(f'Меню администратора', reply_markup=builder.as_markup())
    else:
        await message.answer('У вас нет прав на использование этой команды')


@dp.callback_query(MyCallback.filter(F.action == "def_menu"))
async def ch_rasp_date(callback: types.CallbackQuery, callback_data: MyCallback):
    response = ''
    if callback_data.val == 'База расписания':
        data = write_data()
        file_update_text = data.get("Файл обновлен", "")
        lines = file_update_text.split("\n")
        last_3_dates = lines[-3:]
        # Разделяем текст по символу новой строки и выбираем последние 3 элементам
        response = "Даты обновлений\n\n" + "\n".join(last_3_dates)
    elif callback_data.val == 'Список пользователей':
        data_user = write_users()
        ls_users = [str(i) + '-' + str(j) for i, j in data_user.items()]
        response = f'Пользователей в базе - {len(ls_users)} человек\n\n'
        response += '\n'.join(ls_users)
    elif callback_data.val == 'Температура сервера':
        try:
            temperature_info = psutil.sensors_temperatures(fahrenheit=False)
            if "coretemp" in temperature_info:
                core_temp = temperature_info["coretemp"]
                response = ""
                for entry in core_temp:
                    response += f"Температура {entry.label}: {entry.current}°C\n"
            else:
                response = "Информация о температуре не доступна."
        except AttributeError:
            response = "Модуль psutil не поддерживает получение информации о температуре."
    await callback.message.answer(response)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
