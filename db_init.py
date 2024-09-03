# Абоненты (Код абонента, Номер телефона, ИНН, Адрес).
# Города (Код города, Название, Тариф дневной, Тариф ночной).
# Переговоры (Код переговоров, Код абонента, Код города, Дата, Количество минут, Время суток).
import sqlite3
from random import randint, shuffle, choice
import os

city_count = 100
caller_count = 1_000
conversation_count = 10_000

with open('cities.txt', encoding='utf-8') as file:
    cities = list(map(str.strip, file.readlines()))
shuffle(cities)

os.remove('data.db')

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
    '''DELETE FROM callers
    ''',
    f'''INSERT INTO callers(phone_number, tin, address) VALUES
        {','.join(f'("89{randint(10 ** 8, 10 ** 9 - 1):09}", '
                  f'"{randint(10 ** 11, 10 ** 12 - 1):012}",'
                  f'"{choice(cities)}")' for _ in range(caller_count))}
    ''',
    '''DELETE FROM cities
    ''',
    f'''INSERT INTO cities(name, day_rate, night_rate) VALUES
        {','.join(f'("{city}", {randint(1, 20)}, {randint(1, 20)})' for city in cities)}
    ''',
    '''DELETE FROM conversations
    ''',
    f'''INSERT INTO conversations (caller_id, city_id, date, minute_number, time) VALUES
        {','.join(f'({randint(1, caller_count)}, {randint(1, city_count)},'
                  f'"{randint(1, 12):02}.{randint(1, 28):02}.{randint(2000, 2024)}",'
                  f'{randint(1, 3 * 60)}, "{randint(0, 23):02}:{randint(0, 59):02}")'
                  for _ in range(conversation_count))}
    ''',
]
for command in commands:
    try:
        cursor.execute(command)
    except sqlite3.OperationalError as error:
        print(error)
        print(command)

connection.commit()
connection.close()
