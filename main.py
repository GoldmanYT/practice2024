import sys
import sqlite3
from consts import *
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox, QDialog
from main_window import Ui_MainWindow as MainWindowUi
from search_window import Ui_Dialog as SearchWindowUi


class MainWindow(MainWindowUi, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
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
        for i, table in enumerate(self.tables):
            table.itemChanged.connect(self.check_table_value)
        self.current_table = self.table_callers
        self.file_saved = True
        self.file_created = False

        self.action_on_new()

    def action_on_new(self):
        fill_table_with_data(self.table_callers, [HEADERS_CALLERS])
        fill_table_with_data(self.table_cities, [HEADERS_CITIES])
        fill_table_with_data(self.table_conversations, [HEADERS_CONVERSATIONS])

        caption = 'Без имени.db'
        self.setWindowTitle(f'Учёт телефонных переговоров - {caption}')

    def action_on_open(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Открыть', '.', 'Базы данных (*.db)')
        if not filename:
            return

        for table in self.tables:
            table.itemChanged.disconnect(self.check_table_value)

        *_, caption = filename.split('/')
        self.setWindowTitle(f'Учёт телефонных переговоров - {caption}')

        connection = sqlite3.connect(filename)
        cursor = connection.cursor()

        data_callers = cursor.execute('SELECT * FROM callers').fetchall()
        data_cities = cursor.execute('SELECT * FROM cities').fetchall()
        data_conversations = cursor.execute('SELECT * FROM conversations').fetchall()

        connection.close()

        data_callers.insert(0, HEADERS_CALLERS)
        fill_table_with_data(self.table_callers, data_callers)

        data_cities.insert(0, HEADERS_CITIES)
        fill_table_with_data(self.table_cities, data_cities)

        data_conversations.insert(0, HEADERS_CONVERSATIONS)
        fill_table_with_data(self.table_conversations, data_conversations)

        for table in self.tables:
            table.itemChanged.connect(self.check_table_value)

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
        def update_first_incorrect_cell(table_i, cell_row, cell_col):
            nonlocal first_incorrect_cell
            if first_incorrect_cell == (-1, -1, -1):
                first_incorrect_cell = table_i, cell_row, cell_col

        status = DATA_CORRECT
        first_incorrect_cell = -1, -1, -1
        for i, table in enumerate(self.tables):
            table.itemChanged.disconnect(self.check_table_value)
            for row in range(1, table.rowCount()):
                for col in range(table.columnCount()):
                    if not self.check_table_value(table.item(row, col), table, do_reconnect=False,
                                                  check_unique=False, check_foreign_key=False):
                        status = DATA_FORMAT_ERROR
                        update_first_incorrect_cell(i, row, col)

        for i, table in enumerate(self.tables):
            ids = set()
            for row in range(1, table.rowCount()):
                item = table.item(row, ID_COLUMN)
                text = item.text()
                if text in ids:
                    status = DATA_UNIQUE_ERROR
                    update_first_incorrect_cell(i, row, ID_COLUMN)
                    self.item_change_color(item, table, RED, do_reconnect=False)
                ids.add(text)

        caller_ids = [self.table_callers.item(row, ID_COLUMN).text() for row in range(1, self.table_callers.rowCount())]
        city_ids = [self.table_cities.item(row, ID_COLUMN).text() for row in range(1, self.table_cities.rowCount())]
        for row in range(1, self.table_conversations.rowCount()):
            caller_item = self.table_conversations.item(row, CALLER_ID_COLUMN)
            city_item = self.table_conversations.item(row, CITY_ID_COLUMN)
            if caller_item.text() not in caller_ids:
                status = DATA_ID_ERROR
                update_first_incorrect_cell(TABLE_CONVERSATIONS_I, row, CALLER_ID_COLUMN)
                self.item_change_color(caller_item, self.table_conversations, RED, do_reconnect=False)
            if city_item.text() not in city_ids:
                status = DATA_ID_ERROR
                update_first_incorrect_cell(TABLE_CONVERSATIONS_I, row, CITY_ID_COLUMN)
                self.item_change_color(city_item, self.table_conversations, RED, do_reconnect=False)

        for table in self.tables:
            table.itemChanged.connect(self.check_table_value)

        if first_incorrect_cell != (-1, -1, -1):
            i, row, col = first_incorrect_cell
            self.tab_widget.setCurrentIndex(i)
            table = self.current_table
            table.scrollToItem(table.item(row, col))

        return status

    def insert_into_table(self, row):
        table = self.current_table
        default_values = DEFAULT_TABLE_VALUES[self.tables.index(table)]
        try:
            next_id = max(int(table.item(row, 0).text()) for row in range(1, table.rowCount())) + 1
        except ValueError:
            next_id = default_values[0]
        default_values[0] = str(next_id)
        table.insertRow(row)
        for col in range(table.columnCount()):
            table.setItem(row, col, QTableWidgetItem(default_values[col]))

    def action_on_insert(self):
        row = max(self.current_table.currentRow(), 1)
        self.insert_into_table(row)

    def action_on_add(self):
        row = self.current_table.rowCount()
        self.insert_into_table(row)

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

    def check_table_value(self, item, table=None, do_reconnect=True, check_unique=True, check_foreign_key=True):
        if item.row() == 0:
            return

        text = item.text()
        col = item.column()
        if table is None:
            table = self.sender()

        reg_exp = TABLE_REG_EXPRESSIONS[self.tables.index(table)][col]

        if not reg_exp.exactMatch(text):
            self.item_change_color(item, table, RED, do_reconnect)
            return False

        if check_unique and col == ID_COLUMN and \
                [table.item(row, col).text() for row in range(1, table.rowCount())].count(text) > 1:
            self.item_change_color(item, table, RED, do_reconnect)
            return False

        if check_foreign_key and table == self.table_conversations and col in (CALLER_ID_COLUMN, CITY_ID_COLUMN):
            if col == CALLER_ID_COLUMN:
                linked_table = self.table_callers
            elif col == CITY_ID_COLUMN:
                linked_table = self.table_cities
            else:
                linked_table = None
            ids = [linked_table.item(row, ID_COLUMN).text() for row in range(1, linked_table.rowCount())]
            if text not in ids:
                self.item_change_color(item, table, RED, do_reconnect)
                return False

        self.item_change_color(item, table, WHITE, do_reconnect)
        return True

    def item_change_color(self, item, table, color, do_reconnect):
        if do_reconnect:
            table.itemChanged.disconnect(self.check_table_value)
        item.setBackground(color)
        if do_reconnect:
            table.itemChanged.connect(self.check_table_value)


class SearchDialog(QDialog, SearchWindowUi):
    def __init__(self, parent, table):
        super().__init__(parent)
        self.setupUi(self)

        data = [get_table_headers(table)] + get_table_data(table)
        fill_table_with_data(self.table, data)
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
        filters = [self.search.item(0, col).text() for col in range(self.column_count)]

        data = [get_table_headers(self.data_table)]
        for row in range(1, self.data_table.rowCount()):
            row_data = [self.data_table.item(row, col).text() for col in range(self.column_count)]
            if all(string in text for text, string in zip(row_data, filters)):
                data.append(row_data)

        fill_table_with_data(self.table, data)

    def edit_table(self, row, col):
        if col == 0:
            return

        item_id = self.table.item(row, ID_COLUMN).text()
        item = self.table.item(row, col)
        text = item.text()

        for row in range(1, self.data_table.rowCount()):
            if self.data_table.item(row, ID_COLUMN).text() == item_id:
                self.data_table.item(row, col).setText(text)


def fill_table_with_data(table, data):
    table.clear()
    rows, cols = len(data), len(data[0])
    table.setRowCount(rows)
    table.setColumnCount(cols)
    font = QFont()
    font.setBold(True)

    for row in range(rows):
        for col in range(cols):
            if row == 0:
                item = QTableWidgetItem(str(data[row][col]))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setFont(font)
                table.setItem(row, col, item)
            else:
                table.setItem(row, col, QTableWidgetItem(str(data[row][col])))


def get_table_data(table):
    return [[table.item(row, col).text() for col in range(table.columnCount())] for row in range(1, table.rowCount())]


def get_table_headers(table):
    return [table.item(0, col).text() for col in range(table.columnCount())]


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
