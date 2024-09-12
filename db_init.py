# Абоненты (Код абонента, Номер телефона, ИНН, Адрес).
# Города (Код города, Название, Тариф дневной, Тариф ночной).
# Переговоры (Код переговоров, Код абонента, Код города, Дата, Количество минут, Время суток).
import sqlite3
from random import randint, choice
import os

city_count = 100
caller_count = 1_000
conversation_count = 10_000

with open('cities.txt', encoding='utf-8') as file:
    cities = sorted(map(str.strip, file.readlines()))

try:
    os.remove('data.db')
except FileNotFoundError:
    pass

connection = sqlite3.connect('data.db')
cursor = connection.cursor()

commands = [
    '''CREATE TABLE IF NOT EXISTS callers (
        caller_id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number INTEGER NOT NULL,
        tin INTEGER NOT NULL,
        address TEXT NOT NULL
    )
    ''',
    '''CREATE TABLE IF NOT EXISTS cities (
        city_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        day_rate INTEGER NOT NULL,
        night_rate INTEGER NOT NULL
    )
    ''',
    '''CREATE TABLE IF NOT EXISTS conversations (
        conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        caller_id INTEGER NOT NULL,
        city_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        minute_number INTEGER NOT NULL,
        time TEXT NOT NULL,
        FOREIGN KEY (caller_id) REFERENCES callers(caller_id),
        FOREIGN KEY (city_id) REFERENCES callers(city_id)
    )
    ''',
]
for command in commands:
    try:
        cursor.execute(command)
    except sqlite3.OperationalError as error:
        print(error)
        print(command)
commands = [
    f'''INSERT INTO callers(phone_number, tin, address)
    VALUES (?, ?, ?)
    ''',
    f'''INSERT INTO cities(name, day_rate, night_rate)
    VALUES (?, ?, ?)
    ''',
    f'''INSERT INTO conversations (caller_id, city_id, date, minute_number, time)
    VALUES (?, ?, ?, ?, ?)
    ''',
]
datas = [
    [['89' + ''.join(str(randint(0, 9)) for _ in range(9)),
      str(randint(1, 9)) + ''.join(str(randint(0, 9)) for _ in range(11)),
      choice(cities)]
     for _ in range(caller_count)],
    [[city, randint(1, 20), randint(1, 20)]
     for city in cities],
    [[randint(1, caller_count),
      randint(1, city_count),
      f'{randint(1, 28):02}.{randint(1, 12):02}.{randint(2000, 2024)}',
      randint(1, 3 * 60),
      f'{randint(0, 23):02}:{randint(0, 59):02}']
     for _ in range(conversation_count)],
]
for command, data in zip(commands, datas):
    cursor.executemany(command, data)

connection.commit()
connection.close()
