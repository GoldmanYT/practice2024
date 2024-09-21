from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import QRegExp
from date_check import DateCheck

WHITE = QBrush(QColor(0xFFFFFF))
RED = QBrush(QColor(0xFFC7CE))

ID_COLUMN = 0
CALLER_ID_COLUMN = 1
CITY_ID_COLUMN = 2
TABLE_CONVERSATIONS_I = 2

(DATA_CORRECT,
 DATA_FORMAT_ERROR,
 DATA_UNIQUE_ERROR,
 DATA_ID_ERROR,
 OPERATION_ERROR) = range(5)
ERROR_MESSAGES = {
    DATA_CORRECT: 'Файл успешно сохранён',
    DATA_FORMAT_ERROR: 'Неверный формат данных',
    DATA_UNIQUE_ERROR: 'Код повторяется',
    DATA_ID_ERROR: 'Код отсутствует в связанной таблице',
    OPERATION_ERROR: 'Ошибка: '
}

HEADERS_CALLERS = 'Код абонента', 'Номер телефона', 'ИНН', 'Адрес'
HEADERS_CITIES = 'Код города', 'Название', 'Тариф дневной', 'Тариф ночной'
HEADERS_CONVERSATIONS = 'Код переговоров', 'Код абонента', 'Код города', 'Дата', 'Количество минут', 'Время суток'

DEFAULT_TABLE_VALUES = (
    ['1', '89000000000', '000000000000', 'Введите адрес'],
    ['1', 'Введите город', '0', '0'],
    ['1', '1', '1', '01.01.0001', '0', 'день']
)

TABLE_REG_EXPRESSIONS = (
    tuple(QRegExp(reg_exp) for reg_exp in ('[0-9]{1,}', '8[0-9]{10}', '[0-9]{12}', '.{3,}')),
    tuple(QRegExp(reg_exp) for reg_exp in ('[0-9]{1,}', '.{3,}', '[0-9]{1,}', '[0-9]{1,}')),
    tuple(QRegExp(reg_exp) if reg_exp != 'DATE_CHECK' else DateCheck() for reg_exp in (
        '[0-9]{1,}', '[0-9]{1,}', '[0-9]{1,}', 'DATE_CHECK', '[0-9]{1,}', '(день|ночь)'))
)
