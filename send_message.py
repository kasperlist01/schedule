import requests
import sqlite3
from config import token


def send_telegram_message(chat_id, message, bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }

    response = requests.post(url, data=payload)
    return response.json()


connection = sqlite3.connect('timetable.db')
cursor = connection.cursor()
bot_token = token
select_query = 'SELECT ID_канала FROM Users;'
cursor.execute(select_query)
users = cursor.fetchall()
users = [user[0] for user in users]

message = """📢 Внимание студенты и пользователи! 
 
Мы рады сообщить вам об обновлениях в нашем телеграмм боте! Теперь доступно не только расписание колледжа РАНХиГС, но и Академии РАНХиГС. Это означает, что вы можете получать актуальную информацию о занятиях и событиях не только для студентов колледжа, но и для студентов Академии. 
 
Кроме того, мы обновили интерфейс пользования, чтобы сделать его более удобным и интуитивно понятным для вас. Теперь вы легко найдете нужную информацию и сможете быстро получить ответы на свои вопросы. 
 
Благодарим вас за ваше внимание и оставайтесь с нами для получения свежих обновлений и полезной информации о вашем учебном заведении! 🎓📚"""

for num, chat_id in enumerate(users, 1):
    send_telegram_message(chat_id=chat_id, message=message, bot_token=token)
    print(num)