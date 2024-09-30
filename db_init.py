# Абоненты (Код абонента, Номер телефона, ИНН, Адрес).
# Города (Код города, Название, Тариф дневной, Тариф ночной).
# Переговоры (Код переговоров, Код абонента, Код города, Дата, Количество минут, Время суток).
import sqlite3
from random import randint, choice
import os

from consts import DB_CREATE_REQUESTS, DB_DELETE_REQUESTS, DB_INSERT_REQUESTS

city_count = 100
caller_count = 1_000
conversation_count = 1_000

with open('cities.txt', encoding='utf-8') as file:
    cities = sorted(map(str.strip, file.readlines()))

try:
    os.remove('data.db')
except FileNotFoundError:
    pass

connection = sqlite3.connect('data.db')
cursor = connection.cursor()

for command in DB_CREATE_REQUESTS + DB_DELETE_REQUESTS:
    try:
        cursor.execute(command)
    except sqlite3.OperationalError as error:
        print(error)
        print(command)

datas = [
    [[item_id + 1,
      '89' + ''.join(str(randint(0, 9)) for _ in range(9)),
      str(randint(1, 9)) + ''.join(str(randint(0, 9)) for _ in range(11)),
      choice(cities)]
     for item_id in range(caller_count)],
    [[item_id + 1, city, randint(1, 20), randint(1, 20)]
     for item_id, city in enumerate(cities)],
    [[item_id + 1,
      randint(1, caller_count),
      randint(1, city_count),
      f'{randint(1, 28):02}.{randint(1, 12):02}.{randint(2000, 2024)}',
      randint(1, 3 * 60),
      choice(('день', 'ночь'))]
     for item_id in range(conversation_count)],
]
for command, data in zip(DB_INSERT_REQUESTS, datas):
    cursor.executemany(command, data)

connection.commit()
connection.close()
