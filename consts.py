from PyQt5.QtGui import QBrush, QColor

WHITE = QBrush(QColor(0xFFFFFF))
RED = QBrush(QColor(0xFFC7CE))

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
