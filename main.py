import sys
import sqlite3
from consts import *
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox
from main_window import Ui_MainWindow as MainWindowUi


class MainWindow(MainWindowUi, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('icon.ico'))

        self.action_new.triggered.connect(self.action_on_new)
        self.action_open.triggered.connect(self.action_on_open)
        self.action_save.triggered.connect(self.action_on_save)
        self.action_exit.triggered.connect(self.close)
        self.action_add.triggered.connect(self.action_on_add)
        self.action_delete.triggered.connect(self.action_on_delete)
        self.action_search.triggered.connect(self.action_on_search)

        self.tables = [self.table_callers, self.table_cities, self.table_conversations]
        self.searches = [self.search_callers, self.search_cities, self.search_conversations]
        self.results = [self.result_callers, self.result_cities, self.result_conversations]

        for table, search, result in zip(self.tables, self.searches, self.results):
            table.itemChanged.connect(self.check_table_value)
            search.cellChanged.connect(self.update_result)
            result.cellChanged.connect(self.edit_table)

        self.action_on_new()
        self.action_on_search(self.action_search.isChecked())

    def action_on_new(self):
        for table, headers in zip(self.tables, HEADERS):
            fill_table_with_data(table, [headers])

        caption = NO_NAME
        self.setWindowTitle(f'{WINDOW_TITLE}{caption}')

        self.action_on_search(False)
        self.action_search.setChecked(False)

    def action_on_open(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Открыть', '.', 'Базы данных (*.db)')
        if not filename:
            return

        for table in self.tables:
            table.itemChanged.disconnect(self.check_table_value)

        *_, caption = filename.split('/')
        self.setWindowTitle(f'{WINDOW_TITLE}{caption}')

        connection = sqlite3.connect(filename)
        cursor = connection.cursor()

        data_tables = [
            cursor.execute('SELECT * FROM callers').fetchall(),
            cursor.execute('SELECT * FROM cities').fetchall(),
            cursor.execute('SELECT * FROM conversations').fetchall()
        ]

        connection.close()

        for data, headers, table in zip(data_tables, HEADERS, self.tables):
            data.insert(0, headers)
            fill_table_with_data(table, data)
            table.itemChanged.connect(self.check_table_value)

        self.action_on_search(False)
        self.action_search.setChecked(False)

    def action_on_save(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Сохранить', '', 'Базы данных (*.db)')
        if not filename:
            return

        status = self.check_for_errors()

        try:
            if status == DATA_CORRECT:
                data_tables = [[[table.item(row, col).text()
                                 for col in range(table.columnCount())]
                                for row in range(1, table.rowCount())]
                               for table in self.tables]

                *_, caption = filename.split('/')
                self.setWindowTitle(f'{WINDOW_TITLE}{caption}')

                connection = sqlite3.connect(filename)
                cursor = connection.cursor()

                for request in DB_CREATE_REQUESTS:
                    cursor.execute(request)

                for request in DB_DELETE_REQUESTS:
                    cursor.execute(request)

                for request, data in zip(DB_INSERT_REQUESTS, data_tables):
                    cursor.executemany(request, data)

                connection.commit()
                connection.close()
        except sqlite3.Error as e:
            status = OPERATION_ERROR
            message = ERROR_MESSAGES.get(status) + f'{e}'
        else:
            message = ERROR_MESSAGES.get(status)

        self.show_message(message)

        self.action_on_search(False)
        self.action_search.setChecked(False)

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
            table = self.tables[self.tab_widget.currentIndex()]
            table.scrollToItem(table.item(row, col))

        return status

    def action_on_add(self):
        index = self.tab_widget.currentIndex()
        if self.action_search.isChecked():
            for table in (self.tables[index], self.results[index]):
                row = table.rowCount()
                insert_into_table(row, table, index)
        else:
            table = self.tables[index]
            row = table.rowCount()
            insert_into_table(row, table, index)

    def action_on_delete(self):
        if self.action_search.isChecked():
            table = self.results[self.tab_widget.currentIndex()]
        else:
            table = self.tables[self.tab_widget.currentIndex()]
        row = table.currentRow()
        item_id = table.item(row, ID_COLUMN).text()
        if row != 0:
            table.removeRow(row)
        if self.action_search.isChecked():
            table = self.tables[self.tab_widget.currentIndex()]
            for row in range(1, table.rowCount()):
                if table.item(row, ID_COLUMN).text() == item_id:
                    table.removeRow(row)
                    break

    def action_on_search(self, checked):
        status = self.check_for_errors()

        if status == DATA_CORRECT or not checked:
            if checked:
                for table in self.tables:
                    table.hide()
                for table, search, result in zip(self.tables, self.searches, self.results):
                    search.show()
                    search.cellChanged.disconnect(self.update_result)
                    fill_table_with_data(search, [['' for _ in range(table.columnCount())]], with_headers=False)
                    search.cellChanged.connect(self.update_result)

                    result.cellChanged.disconnect(self.edit_table)
                    result.show()
                    data = [get_table_headers(table)] + get_table_data(table)
                    fill_table_with_data(result, data)
                    result.cellChanged.connect(self.edit_table)
            else:
                for table in self.tables:
                    table.show()
                for search, result in zip(self.searches, self.results):
                    search.hide()
                    result.hide()
        else:
            self.action_search.setChecked(False)
            message = ERROR_MESSAGES.get(status)
            self.show_message(message)

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

    def update_result(self, *_, search=None):
        if search is None:
            search = self.sender()
        index = self.searches.index(search)
        table = self.tables[index]
        column_count = table.columnCount()
        filters = [search.item(0, col).text() for col in range(column_count)]

        data = [get_table_headers(table)]
        for row in range(1, table.rowCount()):
            row_data = [table.item(row, col).text() for col in range(column_count)]
            if all(string.lower() in text.lower() for text, string in zip(row_data, filters)):
                data.append(row_data)

        fill_table_with_data(self.results[index], data)

    def edit_table(self, row, col, result=None):
        if col == 0:
            return

        if result is None:
            result = self.sender()
        index = self.results.index(result)
        table = self.tables[index]
        item_id = result.item(row, ID_COLUMN).text()
        item = result.item(row, col)
        text = item.text()

        for row in range(1, table.rowCount()):
            if table.item(row, ID_COLUMN).text() == item_id:
                table.item(row, col).setText(text)


def fill_table_with_data(table, data, with_headers=True):
    table.clear()
    rows, cols = len(data), len(data[0])
    table.setRowCount(rows)
    table.setColumnCount(cols)
    font = QFont()
    font.setBold(True)

    for row in range(rows):
        for col in range(cols):
            if row == 0 and with_headers:
                item = QTableWidgetItem(str(data[row][col]))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setFont(font)
                table.setItem(row, col, item)
            else:
                table.setItem(row, col, QTableWidgetItem(str(data[row][col])))


def insert_into_table(row, table, index):
    default_values = DEFAULT_TABLE_VALUES[index]
    try:
        next_id = max(int(table.item(row, 0).text()) for row in range(1, table.rowCount())) + 1
    except ValueError:
        next_id = default_values[0]
    default_values[0] = str(next_id)
    table.insertRow(row)
    for col in range(table.columnCount()):
        table.setItem(row, col, QTableWidgetItem(default_values[col]))


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
