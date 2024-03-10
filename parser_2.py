import datetime
import locale
import sqlite3
from typing import List, Tuple

class Database:
    def __init__(self):
        self.connection = sqlite3.connect('timetable.db')
        self.cursor = self.connection.cursor()

    def get_groups_by_faculty(self, faculty: str) -> List[str]:
        """Возвращает список групп, принадлежащих заданному факультету."""
        select_query = 'SELECT Группа FROM Schedule WHERE Факультет LIKE ? GROUP BY Группа;'
        self.cursor.execute(select_query, (f'%{faculty}%',))
        groups = self.cursor.fetchall()
        return [group[0] for group in groups]
    
    def add_or_update_user(self, name, group, channel_id):
        self.cursor.execute("SELECT ID FROM main.Users WHERE ID_канала = ?", (channel_id,))
        result = self.cursor.fetchone()

        if result:
            self.cursor.execute("UPDATE main.Users SET Группа = ? WHERE ID_канала = ?", (group, channel_id))
        else:
            self.cursor.execute("INSERT INTO main.Users (Имя, Группа, Дата_регестрации, ID_канала) VALUES (?, ?, ?, ?)",
                             (name, group, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), channel_id))
        self.connection.commit()

    def get_schedule_by_date(self, group: str, target_date: datetime.date) -> str:
        """Возвращает расписание для указанной группы на заданную дату."""
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        date_str = target_date.strftime("%d %B").capitalize()
        self.cursor.execute(
            "SELECT Расписание FROM Schedule WHERE Группа = ? AND Дата LIKE ?",
            (group, f"%{date_str}%")
        )
        schedule = self.cursor.fetchone()
        if schedule:
            return schedule[0]
        else:
            return "Расписание на этот день не найдено."
        
    def get_group_by_channel_id(self, channel_id):
        """Возвращает группу по id канала пользователя."""
        self.cursor.execute(
            "select Группа from Users where ID_канала = ?",
            (channel_id,)
        )
        group = self.cursor.fetchone()
        return group[0]
    
    def get_list_users(self):
        self.cursor.execute(
            "SELECT Имя, ID_канала, Группа, strftime('%d.%m.%Y', Дата_регестрации) as Дата_регестрации FROM Users"
        )
        users = self.cursor.fetchall()

        formatted_users = []
        for user in users:
            name, channel_id, group, registration_date = user
            formatted_user = f"👤 Имя: {name}\n" \
                            f"🆔 ID канала: {channel_id}\n" \
                            f"🎓 Группа: {group}\n" \
                            f"📅 Дата регистрации: {registration_date}\n"
            formatted_users.append(formatted_user)

        return formatted_users
    
    def fetch_check_dates(self, faculty):
        self.cursor.execute(
            "SELECT Дата_проверки FROM Schedule WHERE LOWER(Факультет) LIKE LOWER(?) GROUP BY Дата_проверки ORDER BY Дата_проверки DESC LIMIT 1;",
            (f"%{faculty}%",)
        )
        result = self.cursor.fetchone()
        if result:
            date_str = result[0]
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            date_obj += datetime.timedelta(hours=3)
            formatted_date = date_obj.strftime("%H:%M:%S")
            return formatted_date
        else:
            return "Дата не найдена"





    def close(self):
        """Закрывает соединение с базой данных."""
        self.connection.close()
