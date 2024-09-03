import sys
import sqlite3
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTableWidgetItem, QWidget, QDialog, QCheckBox


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)

        self.action_new.triggered.connect(self.action_on_new)
        self.action_open.triggered.connect(self.action_on_open)
        self.action_save.triggered.connect(self.action_on_save)
        self.action_exit.triggered.connect(self.close)
        self.action_insert.triggered.connect(self.action_on_insert)
        self.action_add.triggered.connect(self.action_on_add)
        self.action_delete.triggered.connect(self.action_on_delete)

        self.tab_widget.currentChanged.connect(self.current_tab_changed)

        self.tables = [self.table_callers, self.table_cities, self.table_conversations]
        self.current_table = self.table_callers
        self.file_saved = True
        self.file_created = False

        self.action_on_new()

    def action_on_new(self):
        data_callers = [('Код абонента', 'Номер телефона', 'ИНН', 'Адрес')]
        self.fill_table_with_data(self.table_callers, data_callers)

        data_cities = [('Код города', 'Название', 'Тариф дневной', 'Тариф ночной')]
        self.fill_table_with_data(self.table_cities, data_cities)

        data_conversations = [(
            'Код переговоров', 'Код абонента', 'Код города', 'Дата', 'Количество минут', 'Время суток')]
        self.fill_table_with_data(self.table_conversations, data_conversations)

        caption = 'Без имени.db'
        self.setWindowTitle(f'Учёт телефонных переговоров - {caption}')

    def action_on_open(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Открыть', '.', 'Базы данных (*.db)')
        if not filename:
            return

        *_, caption = filename.split('/')
        self.setWindowTitle(f'Учёт телефонных переговоров - {caption}')

        connection = sqlite3.connect(filename)
        cursor = connection.cursor()

        data_callers = cursor.execute('SELECT * FROM callers').fetchall()
        data_cities = cursor.execute('SELECT * FROM cities').fetchall()
        data_conversations = cursor.execute('SELECT * FROM conversations').fetchall()

        connection.close()

        data_callers.insert(0, ('Код абонента', 'Номер телефона', 'ИНН', 'Адрес'))
        self.fill_table_with_data(self.table_callers, data_callers)

        data_cities.insert(0, ('Код города', 'Название', 'Тариф дневной', 'Тариф ночной'))
        self.fill_table_with_data(self.table_cities, data_cities)

        data_conversations.insert(0, (
            'Код переговоров', 'Код абонента', 'Код города', 'Дата', 'Количество минут', 'Время суток'))
        self.fill_table_with_data(self.table_conversations, data_conversations)

    def action_on_save(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Сохранить', '', 'Базы данных (*.db)')
        if not filename:
            return

        *_, caption = filename.split('/')
        self.setWindowTitle(f'Учёт телефонных переговоров - {caption}')

        data_callers = [[self.table_callers.item(row, col).text()
                         for col in range(self.table_callers.columnCount())]
                        for row in range(1, self.table_callers.rowCount())]

        data_cities = [[self.table_cities.item(row, col).text()
                        for col in range(self.table_cities.columnCount())]
                       for row in range(1, self.table_cities.rowCount())]

        data_conversations = [[self.table_conversations.item(row, col).text()
                               for col in range(self.table_conversations.columnCount())]
                              for row in range(1, self.table_conversations.rowCount())]

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

    def action_on_insert(self):
        row = max(self.current_table.currentRow(), 1)
        self.current_table.insertRow(row)

    def action_on_add(self):
        self.current_table.insertRow(self.current_table.rowCount())

    def action_on_delete(self):
        row = self.current_table.currentRow()
        if row != 0:
            self.current_table.removeRow(row)

    def current_tab_changed(self, index):
        self.current_table = self.tables[index]

    def fill_table_with_data(self, table, data):
        table.clear()
        rows, cols = len(data), len(data[0])
        table.setRowCount(rows)
        table.setColumnCount(cols)
        for row in range(rows):
            for col in range(cols):
                if row == 0:
                    table.setCellWidget(row, col, Header(self, str(data[row][col]), table, col))
                else:
                    table.setItem(row, col, QTableWidgetItem(str(data[row][col])))
        table.resizeColumnsToContents()
        table.resizeRowToContents(0)


class Header(QWidget):
    def __init__(self, parent, name, table, col):
        super().__init__(parent)
        uic.loadUi('header.ui', self)

        self.header_name.setText(name)
        self.tool_button.clicked.connect(self.open_dialog)

        self.main_window = parent
        self.table = table
        self.col = col

    def get_filters(self):
        return sorted(set(self.table.item(row, self.col).text() for row in range(1, self.table.rowCount())))

    def get_data(self):
        return [[self.table.item(row, col).text()
                 for col in range(self.table.columnCount())]
                for row in range(1, self.table.rowCount())]

    def open_dialog(self):
        filter_dialog = FilterDialog(self, self.get_filters())
        filter_dialog.exec()
        if filter_dialog.result() != QDialog.Accepted:
            return
        filters = {combo_box.text() for combo_box in filter_dialog.check_boxes if combo_box.isChecked()}
        data = self.get_data()
        new_data = [[self.table.cellWidget(0, col).header_name.text() for col in range(self.table.columnCount())]]
        for row in range(len(data)):
            if str(data[row][self.col]) in filters:
                new_data.append(data[row])
        self.main_window.fill_table_with_data(self.table, new_data)


class FilterDialog(QDialog):
    def __init__(self, parent, filters):
        super().__init__(parent)
        uic.loadUi('filter_dialog.ui', self)

        self.check_box_all.stateChanged.connect(self.toggle_all)
        self.line_edit_search.textChanged.connect(self.search)

        self.check_boxes = []
        for item in filters:
            check_box = QCheckBox(item, self)
            check_box.setChecked(True)
            self.check_boxes.append(check_box)
            self.content_layout.addWidget(check_box)

    def toggle_all(self, state):
        for check_box in self.check_boxes:
            if check_box.isHidden():
                check_box.setChecked(False)
            else:
                check_box.setChecked(state)

    def search(self):
        text = self.line_edit_search.text()
        if not text:
            self.check_box_all.setChecked(True)
        for check_box in self.check_boxes:
            if not text or text.lower() in check_box.text().lower():
                check_box.show()
                check_box.setChecked(True)
            else:
                check_box.hide()
                check_box.setChecked(False)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
