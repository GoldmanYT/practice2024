import sys
import sqlite3
from consts import *
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QWidget, QMessageBox, QDialog
from fnmatch import fnmatch
from header import Ui_Form as HeaderUi
from main_window import Ui_MainWindow as MainWindowUi
from search_window import Ui_Dialog as SearchWindowUi


class MainWindow(QMainWindow, MainWindowUi):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.setWindowIcon(QIcon('icon.ico'))

        self.action_new.triggered.connect(self.action_on_new)
        self.action_open.triggered.connect(self.action_on_open)
        self.action_save.triggered.connect(self.action_on_save)
        self.action_exit.triggered.connect(self.close)
        self.action_insert.triggered.connect(self.action_on_insert)
        self.action_add.triggered.connect(self.action_on_add)
        self.action_delete.triggered.connect(self.action_on_delete)
        self.action_search.triggered.connect(self.action_on_search)

        self.tab_widget.currentChanged.connect(self.current_tab_changed)

        self.tables = [self.table_callers, self.table_cities, self.table_conversations]
        for table in self.tables:
            table.itemChanged.connect(self.check_table_value)
            table.itemChanged.connect(table.resizeColumnsToContents)
        self.current_table = self.table_callers
        self.file_saved = True
        self.file_created = False

        self.action_on_new()

    def action_on_new(self):
        fill_table_with_data(self, self.table_callers, [HEADERS_CALLERS])
        fill_table_with_data(self, self.table_cities, [HEADERS_CITIES])
        fill_table_with_data(self, self.table_conversations, [HEADERS_CONVERSATIONS])

        caption = 'Без имени.db'
        self.setWindowTitle(f'Учёт телефонных переговоров - {caption}')

    def action_on_open(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Открыть', '.', 'Базы данных (*.db)')
        if not filename:
            return

        for table in self.tables:
            table.itemChanged.disconnect(self.check_table_value)
            table.itemChanged.disconnect(table.resizeColumnsToContents)

        *_, caption = filename.split('/')
        self.setWindowTitle(f'Учёт телефонных переговоров - {caption}')

        connection = sqlite3.connect(filename)
        cursor = connection.cursor()

        data_callers = cursor.execute('SELECT * FROM callers').fetchall()
        data_cities = cursor.execute('SELECT * FROM cities').fetchall()
        data_conversations = cursor.execute('SELECT * FROM conversations').fetchall()

        connection.close()

        data_callers.insert(0, HEADERS_CALLERS)
        fill_table_with_data(self, self.table_callers, data_callers)

        data_cities.insert(0, HEADERS_CITIES)
        fill_table_with_data(self, self.table_cities, data_cities)

        data_conversations.insert(0, HEADERS_CONVERSATIONS)
        fill_table_with_data(self, self.table_conversations, data_conversations)

        for table in self.tables:
            table.itemChanged.connect(self.check_table_value)
            table.itemChanged.connect(table.resizeColumnsToContents)

    def action_on_save(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Сохранить', '', 'Базы данных (*.db)')
        if not filename:
            return

        status = self.check_for_errors()

        try:
            if status == DATA_CORRECT:
                data_callers = [[self.table_callers.item(row, col).text()
                                 for col in range(self.table_callers.columnCount())]
                                for row in range(1, self.table_callers.rowCount())]

                data_cities = [[self.table_cities.item(row, col).text()
                                for col in range(self.table_cities.columnCount())]
                               for row in range(1, self.table_cities.rowCount())]

                data_conversations = [[self.table_conversations.item(row, col).text()
                                       for col in range(self.table_conversations.columnCount())]
                                      for row in range(1, self.table_conversations.rowCount())]

                *_, caption = filename.split('/')
                self.setWindowTitle(f'Учёт телефонных переговоров - {caption}')

                connection = sqlite3.connect(filename)
                cursor = connection.cursor()

                cursor.execute('''CREATE TABLE IF NOT EXISTS callers (
                                      caller_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                      phone_number INTEGER NOT NULL,
                                      tin INTEGER NOT NULL,
                                      address TEXT NOT NULL
                                  )''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS cities (
                                      city_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                      name TEXT NOT NULL,
                                      day_rate INTEGER NOT NULL,
                                      night_rate INTEGER NOT NULL
                                  )''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS conversations (
                                      conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                      caller_id INTEGER NOT NULL,
                                      city_id INTEGER NOT NULL,
                                      date TEXT NOT NULL,
                                      minute_number INTEGER NOT NULL,
                                      time TEXT NOT NULL,
                                      FOREIGN KEY (caller_id) REFERENCES callers(caller_id),
                                      FOREIGN KEY (city_id) REFERENCES callers(city_id)
                                  )''')

                cursor.execute('DELETE FROM callers')
                cursor.execute('DELETE FROM cities')
                cursor.execute('DELETE FROM conversations')

                sqlite_insert_query = '''INSERT INTO callers
                                         (caller_id, phone_number, tin, address)
                                         VALUES (?, ?, ?, ?);'''
                cursor.executemany(sqlite_insert_query, data_callers)

                sqlite_insert_query = '''INSERT INTO cities
                                         (city_id, name, day_rate, night_rate)
                                         VALUES (?, ?, ?, ?);'''
                cursor.executemany(sqlite_insert_query, data_cities)

                sqlite_insert_query = '''INSERT INTO conversations
                                         (conversation_id, caller_id, city_id, date, minute_number, time)
                                         VALUES (?, ?, ?, ?, ?, ?);'''
                cursor.executemany(sqlite_insert_query, data_conversations)

                connection.commit()
                connection.close()
        except sqlite3.Error as e:
            status = OPERATION_ERROR
            message = ERROR_MESSAGES.get(status) + f'{e}'
        else:
            message = ERROR_MESSAGES.get(status)

        self.show_message(message)

    def show_message(self, message):
        message_box = QMessageBox(self)
        message_box.setWindowTitle('Информация')
        message_box.setText(message)
        message_box.exec_()

    def check_for_errors(self):
        status = DATA_CORRECT
        for table in self.tables:
            table.itemChanged.disconnect(self.check_table_value)
            table.itemChanged.disconnect(table.resizeColumnsToContents)
            for row in range(1, table.rowCount()):
                for col in range(table.columnCount()):
                    if not self.check_table_value(table.item(row, col), table, do_reconnect=False):
                        status = DATA_FORMAT_ERROR

        for table in self.tables:
            ids = set()
            for row in range(1, table.rowCount()):
                item = table.item(row, 0)
                text = item.text()
                if text in ids:
                    status = DATA_UNIQUE_ERROR
                    self.item_change_color(item, table, RED, do_reconnect=False)
                ids.add(text)

        caller_ids = [self.table_callers.item(row, 0).text() for row in range(1, self.table_callers.rowCount())]
        city_ids = [self.table_cities.item(row, 0).text() for row in range(1, self.table_cities.rowCount())]
        for row in range(1, self.table_conversations.rowCount()):
            caller_item = self.table_conversations.item(row, 1)
            city_item = self.table_conversations.item(row, 2)
            if caller_item.text() not in caller_ids:
                status = DATA_ID_ERROR
                self.item_change_color(caller_item, self.table_conversations, RED, do_reconnect=False)
            if city_item.text() not in city_ids:
                status = DATA_ID_ERROR
                self.item_change_color(city_item, self.table_conversations, RED, do_reconnect=False)

        for table in self.tables:
            table.itemChanged.connect(self.check_table_value)
            table.itemChanged.connect(table.resizeColumnsToContents)
        return status

    def action_on_insert(self):
        row = max(self.current_table.currentRow(), 1)
        self.current_table.insertRow(row)
        for col in range(self.current_table.columnCount()):
            self.current_table.setItem(row, col, QTableWidgetItem())

    def action_on_add(self):
        row = self.current_table.rowCount()
        self.current_table.insertRow(row)
        for col in range(self.current_table.columnCount()):
            self.current_table.setItem(row, col, QTableWidgetItem())

    def action_on_delete(self):
        row = self.current_table.currentRow()
        if row != 0:
            self.current_table.removeRow(row)

    def action_on_search(self):
        status = self.check_for_errors()

        if status == DATA_CORRECT:
            dialog = SearchDialog(self, self.current_table)
            dialog.exec()
        else:
            message = ERROR_MESSAGES.get(status)
            self.show_message(message)

    def current_tab_changed(self, index):
        self.current_table = self.tables[index]

    def check_table_value(self, item, table=None, do_reconnect=True):
        text = item.text()
        col = item.column()
        if table is None:
            table = self.sender()
        if table is self.table_callers:
            digit_count = {
                0: None,
                1: 11,
                2: 12,
            }
            str_length = {
                3: 3
            }
            if col in digit_count.keys() and not check_int(text, digit_count.get(col)) or \
                    col == 1 and text[:1] != '8' or \
                    col in str_length.keys() and not check_str(text, str_length.get(col)):
                self.item_change_color(item, table, RED, do_reconnect)
                return False
            else:
                self.item_change_color(item, table, WHITE, do_reconnect)
                return True
        elif table is self.table_cities:
            digit_count = {
                0: None,
                2: None,
                3: None,
            }
            str_length = {
                1: 3
            }
            if col in digit_count.keys() and not check_int(text, digit_count.get(col)) or \
                    col in str_length.keys() and not check_str(text, str_length.get(col)):
                self.item_change_color(item, table, RED, do_reconnect)
                return False
            else:
                self.item_change_color(item, table, WHITE, do_reconnect)
                return True
        elif table is self.table_conversations:
            digit_count = {
                0: None,
                1: None,
                2: None,
                4: None,
            }
            str_length = {}
            date_columns = (3,)
            time_columns = (5,)
            if col in digit_count.keys() and not check_int(text, digit_count.get(col)) or \
                    col in date_columns and not check_date(text) or \
                    col in time_columns and not check_time(text) or \
                    col in str_length.keys() and not check_str(text, str_length.get(col)):
                self.item_change_color(item, table, RED, do_reconnect)
                return False
            else:
                self.item_change_color(item, table, WHITE, do_reconnect)
                return True

    def item_change_color(self, item, table, color, do_reconnect):
        if do_reconnect:
            table.itemChanged.disconnect(self.check_table_value)
        item.setBackground(color)
        if do_reconnect:
            table.itemChanged.connect(self.check_table_value)


class Header(QWidget, HeaderUi):
    def __init__(self, parent, name):
        super().__init__(parent)
        uic.loadUi('header.ui', self)

        self.header_name.setText(name)


class SearchDialog(QDialog, SearchWindowUi):
    def __init__(self, parent, table):
        super().__init__(parent)
        uic.loadUi('search.ui', self)

        data = [get_table_headers(table)] + get_table_data(table)
        fill_table_with_data(self, self.table, data)
        self.column_count = table.columnCount()

        self.search.setColumnCount(self.column_count)
        for col in range(self.column_count):
            width = self.table.columnWidth(col)
            self.search.setColumnWidth(col, width)
            self.search.setItem(0, col, QTableWidgetItem())

        self.data_table = table
        self.parent = parent

        self.table.cellChanged.connect(self.edit_table)
        self.search.cellChanged.connect(self.update_table)

    def update_table(self):
        filters = [f'*{text}*' if (text := self.search.item(0, col).text()) else '*'
                   for col in range(self.column_count)]

        data = [get_table_headers(self.data_table)]
        for row in range(1, self.data_table.rowCount()):
            row_data = [self.data_table.item(row, col).text() for col in range(self.column_count)]
            if all(fnmatch(text, pattern) for text, pattern in zip(row_data, filters)):
                data.append(row_data)

        fill_table_with_data(self, self.table, data, resize_table=False)

    def edit_table(self, row, col):
        if col == 0:
            return

        item_id = self.table.item(row, 0).text()
        item = self.table.item(row, col)
        text = item.text()

        for row in range(1, self.data_table.rowCount()):
            if self.data_table.item(row, 0).text() == item_id:
                self.data_table.item(row, col).setText(text)


def fill_table_with_data(parent, table, data, resize_table=True):
    table.clear()
    rows, cols = len(data), len(data[0])
    table.setRowCount(rows)
    table.setColumnCount(cols)
    for row in range(rows):
        for col in range(cols):
            if row == 0:
                table.setCellWidget(row, col, Header(parent, str(data[row][col])))
            else:
                table.setItem(row, col, QTableWidgetItem(str(data[row][col])))
    if resize_table:
        table.resizeColumnsToContents()
        table.resizeRowToContents(0)


def get_table_data(table):
    return [[table.item(row, col).text() for col in range(table.columnCount())] for row in range(1, table.rowCount())]


def get_table_headers(table):
    return [table.cellWidget(0, col).header_name.text() for col in range(table.columnCount())]


def check_int(s, digit_count=None):
    if digit_count is None:
        return s.isdigit()
    return len(s) == digit_count and s.isdigit()


def check_str(s, min_length=None):
    if min_length is None:
        return True
    return len(s) >= min_length


def check_time(s):
    if not (len(s) == 5 and s[2:3] == ':' and
            s[:2].isdigit() and s[3:].isdigit()):
        return False
    return 0 <= int(s[:2]) <= 23 and 0 <= int(s[3:]) <= 59


def check_date(s):
    if not (len(s) == 10 and s[2:3] == '.' and s[5:6] == '.' and
            s[:2].isdigit() and s[3:5].isdigit() and s[6:].isdigit()):
        return False
    days_in_months = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= int(s[3:5]) <= 12 and 1 <= int(s[:2]) <= days_in_months[int(s[3:5])] and 0 <= int(s[6:]) <= 9999


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
