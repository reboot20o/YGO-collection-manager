import sys
import os
if not getattr(sys, 'frozen', False):
    if os.getcwd().__contains__('qt'):
        os.chdir('../../')
    sys.path.append('src')

from modules.create_db import create_connection, select_rows, select_row, insert_row, insert_rows
from modules.location_designation import path, asset_path
from modules.db_remove import get_set, update_tables
from ui import Ui_collector

import requests
from PIL import Image
import datetime

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QImage, QPixmap
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QTableWidgetItem, QMessageBox, QSpinBox)


class Widget(QWidget, Ui_collector):
    def __init__(self):
        super().__init__()
        self.setupUI()

        self.items = 0  # Index to keep track of number of rows in table
        self.detached = []  # Initialize list to hold items detached from table
        db_loc = asset_path('cards.db')  # Get path to database
        self.con, update = create_connection(db_loc)  # Initialize database
        if update:
            update_tables(self.con)  # Re-populates database tables if new update available
        self.set_list = select_rows(self.con, "select set_code, set_name, release from set_list order by release asc;")
        self.pack_list = self.pop_set_list()

        self.add_to_packs()
        self.combo_set()
        self.reset_filter()

        # Signals and slots
        self.set_list_combo.currentTextChanged.connect(self.set_table)
        self.search_edit.returnPressed.connect(self.search)
        self.search_btn.clicked.connect(self.search)
        for key in self.filter_combo:
            self.filter_combo[key].activated.connect(self.set_filter)
        self.reset_btn.clicked.connect(self.reset_filter)
        self.all_check.toggled.connect(self.select_all)
        self.owned_check.toggled.connect(self.remove_select)
        self.table.itemSelectionChanged.connect(self.select_item)
        self.view_set_btn.clicked.connect(self.view_set)
        self.add_set_btn.clicked.connect(self.add_set)
        self.main_sets_check.toggled.connect(self.set_list_filter)
        self.sort_sets_combo.currentTextChanged.connect(self.set_list_filter)
        self.sort_direction_combo.currentTextChanged.connect(self.set_list_filter)
        self.edit_owned_btn.clicked.connect(self.edit_owned)

    @Slot()
    def set_table(self, text):
        """Slot for set_list_combo. Reads current set from combo box then populates table with cards from set."""
        try:
            set_code = text.split()[0]
            state = """select a.id, a.name, a.type, a.archetype, a.race, coalesce(ss.owned,0) as owned, 
                        s.set_rarity_code, s.set_id from all_cards as a left join sets as s on a.name=s.name
                        left outer join set_cards as ss on s.set_id=ss.set_id where s.set_code=? order by s.set_id;"""
            self.add_to_table(state, (set_code,))
        except IndexError:
            pass

    @Slot()
    def search(self):
        """Slot for search_edit. Reads input text from search bar and performs a fuzzy search."""
        text = self.search_edit.text()
        state = """select a.id, a.name, a.type, a.archetype, a.race, sum(coalesce(s.owned, 0)) as owned
                        from all_cards as a left join set_cards as s on a.name=s.name
                        inner join tri(?) as t on a.name=t.name
                        group by a.id, a.name, a.type, a.archetype, a.race
                        order by owned desc nulls last;"""
        self.add_to_table(state, (text,))

    @Slot()
    def set_filter(self):
        """Slot for filter_combo boxes. Read values from combo boxes and filters displayed cards based on result."""
        vals = {}
        for key, val in self.filter_combo.items():
            try:
                vals[key] = val.currentText().split(' - ')[1]
            except IndexError:
                pass
        cond = ' and '.join([f'{field}=?' for field in vals])
        for tag in set(self.filter_combo.keys()).difference(set(vals.keys())):
            if not vals.keys():
                self.reset_filter()
                break
            self.filter_combo[tag].clear()
            rows = select_rows(self.con, """select count({field}), {field} from all_cards where {field} is not null and 
                                            {cond} group by {field} order by {field}""".format(field=tag, cond=cond),
                               tuple(vals.values()))
            for row in rows:
                self.filter_combo[tag].addItem(f'{str(row[0])} - {row[1]}')
            self.filter_combo[tag].insertItem(0, '')
            self.filter_combo[tag].setCurrentIndex(0)
        state = """select a.id, a.name, a.type, a.archetype, a.race, sum(coalesce(s.owned, 0)) as owned 
                        from all_cards as a left join set_cards as s on a.name=s.name 
                        where {cond}
                        group by a.id, a.name, a.type, a.archetype, a.race
                        order by owned desc nulls last;""".format(cond=cond)
        self.add_to_table(state, tuple(vals.values()))

    @Slot()
    def reset_filter(self):
        """Slot for reset_btn. Resets filters."""
        labels = ['Type', 'Race', 'Archetype', 'Attribute', 'Level', 'Linkval']
        for tag in labels:
            self.filter_combo[tag].clear()
            vals = select_rows(self.con, """select count({field}), {field} from all_cards where {field} is not null \
                            group by {field} order by {field}""".format(field=tag.lower()))
            for row in vals:
                self.filter_combo[tag].addItem(f'{str(row[0])} - {row[1]}')
            self.filter_combo[tag].insertItem(0, '')
            self.filter_combo[tag].setCurrentIndex(0)

    @Slot()
    def select_all(self):
        """Slot for all_check. Checks state from check box and populates table with all cards or clears table."""
        self.clear_table(self.table)
        if self.all_check.isChecked():
            state = """select a.id, a.name, a.type, a.archetype, a.race, sum(coalesce(s.owned, 0)) as owned 
                    from all_cards as a left join set_cards as s on a.name=s.name 
                    group by a.id, a.name, a.type, a.archetype, a.race
                    order by owned desc nulls last;"""
            self.add_to_table(state)
        else:
            self.set_list_combo.setCurrentIndex(-1)
            self.summary.setText('Owned: \t-\tUnique: \t-\tAvailable: ')

    @Slot()
    def remove_select(self, checked):
        count = self.table.rowCount()
        if checked:
            for i in range(count):
                if int(self.table.item(i, 5).text()) == 0:
                    self.table.hideRow(i)
        else:
            for i in range(count):
                if self.table.isRowHidden(i):
                    self.table.showRow(i)

    @Slot()
    def select_item(self):
        """Slot for table. Reads selected row from table then populates labels in detail view."""
        self.clear_table(self.cardsets_table)
        self.clear_table(self.bans_list)
        row = self.table.currentIndex().row()
        card_id = self.table.item(row, 0).text()
        info = select_row(self.con, """select a.descript, a.name, a.type, a.attribute, a.race, a.level, a.atk, a.def, 
                                    a.archetype, a.linkval, a.scale, sum(coalesce(s.owned, 0)) as owned  
                                    from all_cards as a left join set_cards as s on a.name=s.name where a.id=?
                                    group by a.name, a.type, a.attribute, a.race, a.archetype, a.level, a.atk, a.def, 
                                    a.linkval, a.scale, a.descript;""", (card_id,))
        sets = select_rows(self.con, """select s.set_id, s.set_rarity_code, coalesce(sc.owned,0) from sets as s 
                                        left join set_cards as sc on s.set_id=sc.set_id where s.id=?""", (card_id,))
        ban_list = select_row(self.con, "select tcg, ocg, goat from banlist where id=?", (card_id,))
        bans = {key: val for key, val in zip(['TCG', 'OCG', 'GOAT'], ban_list) if val is not None}
        # print(info)
        formats = select_rows(self.con, "select format from formats where name=?", (info[1],))
        format_list = {key[0]: '' for key in formats}
        format_list.update(bans)
        card_id = card_id.lstrip('0')
        size = 280, 380
        self.im = QImage(asset_path(f'images/{card_id}.thumbnail'))
        if self.im.isNull():
            print(f'Downloading card art for {info[1]}')
            url = f"https://images.ygoprodeck.com/images/cards/{card_id}.jpg"
            im = Image.open(requests.get(url, stream=True).raw)
            im.thumbnail(size)
            im.save(asset_path(f'images/{card_id}.thumbnail'), 'JPEG')
            self.im.load(asset_path(f'images/{card_id}.thumbnail'))
        self.labels['image'].setPixmap(QPixmap(self.im))
        details = {key: val for key, val in zip(self.tags[1:], info[:-1])}
        for key, val in details.items():
            if key == 'description':
                val = val.replace('\n', '<br>')
            self.labels[key].setText(f'{key.title()}<br><b style="font-size:14px;">{val}</b>')
        self.owned_label.setText(f'Owned:\n{info[-1]}')
        for i in range(len(sets)):
            self.cardsets_table.insertRow(i)
            items = [QTableWidgetItem(str(val)) for val in sets[i]]
            self.cardsets_table.setCellWidget(i, 2, QSpinBox())
            self.cardsets_table.cellWidget(i, 2).setValue(sets[i][2])
            self.cardsets_table.cellWidget(i, 2).setMaximum(10000)
            for j in range(2):
                self.cardsets_table.setItem(i, j, items[j])

        for i, elem in enumerate(format_list.items()):
            self.bans_list.insertRow(i)
            items = [QTableWidgetItem(str(val)) for val in elem]
            for j in range(2):
                self.bans_list.setItem(i, j, items[j])

    @Slot()
    def view_set(self):
        """Slot for view_set_btn. Reads the current pack from pack_list_combo and populates table with cards from set"""
        text = self.pack_list_combo.currentText()
        pack, cards = get_set(text)
        self.set_table(pack[0])

    @Slot()
    def add_set(self):
        """Slot for add_set_btn. Reads current pack from pack_list_combo then adds set and cards to database."""
        text = self.pack_list_combo.currentText()
        self.add_to_database(text)

    @Slot()
    def set_list_filter(self):
        """Slot for main_sets_check. Populates pack_list_combo with sets not in collection."""
        self.pack_list_combo.clear()
        resp = self.pack_list.copy()
        check = ['special', 'participation', 'promotion', 'subscription', 'prize']
        order = {'Asc': False, 'Desc': True}
        key = {'Date': lambda e: (e[3], e[1], e[0]),
               'Set Code': lambda e: (e[1], e[0]),
               'Number of cards': lambda e: (e[2], e[1], e[0])}
        sort_key = self.sort_sets_combo.currentText()
        sort_dir = self.sort_direction_combo.currentText()
        if self.main_sets_check.isChecked():
            resp[:] = [elem for elem in resp if not any(map(elem[0].lower().__contains__, check))]
        if sort_key != 'Sort By':
            resp = sorted(resp, key=key[sort_key], reverse=order[sort_dir])
        self.add_to_packs(resp)

    @Slot()
    def edit_owned(self):
        """Slot for edit_owned_btn. Updates owned cards by reading from spinbox."""
        card = self.table.item(self.table.currentItem().row(), 1).text()
        rows = select_rows(self.con, "select set_id, owned from set_cards where name = ?", (card,))
        check = dict(rows)
        count = self.cardsets_table.rowCount()
        names = [self.cardsets_table.item(row, 0).text() for row in range(count)]
        vals = [self.cardsets_table.cellWidget(row, 2).value() for row in range(count)]
        owned = {name: val for name, val in zip(names, vals)}
        to_add = []
        for key, val in owned.items():
            if key in list(check.keys()) and val != check[key]:
                to_add.append((val, key))
                print(f'The value for {key} changed from {check[key]} to {val}')
            elif key not in list(check.keys()) and val > 0:
                code = key.split('-')[0]
                for row in self.pack_list:
                    if row[1] == code:
                        text = f"{row[1]} - {row[0]} - ({row[3]}) - [{row[2]}]"
                        break
                self.add_to_database(text)
                to_add.append((val, key))
                print(f'Set {key} not in database, but owned is {val}')
        insert_rows(self.con, "update set_cards set owned = ? where set_id = ?", to_add)
        self.select_item()

    def pop_set_list(self):
        sets = {elem[0]: elem[1] for elem in self.set_list}
        resp = select_rows(self.con, "select * from all_sets where date is not null;")
        resp[:] = [elem for elem in resp if
                   (elem[1] not in sets.keys() and elem[0] not in sets.values())]
        return resp

    def add_to_database(self, text):
        """Method adds set and set cards to database."""
        pack, cards = get_set(text)
        insert_row(self.con, "insert into set_list values (?,?,?,?,?)", pack)
        insert_rows(self.con, "insert or ignore into set_cards values (?,?,?,?,?,?)", cards)

        self.set_list = select_rows(self.con, "select set_code, set_name, release from set_list order by release asc;")
        self.pack_list = self.pop_set_list()
        self.add_to_packs()
        self.combo_set()

    def add_to_table(self, state, vals=()):
        """Method queries database with state and populates table with the resultant cards."""
        self.clear_table(self.table)
        self.table.sortByColumn(7, Qt.AscendingOrder)
        self.table.setSortingEnabled(False)
        self.items = 0
        var = self.owned_check.isChecked()
        data = select_rows(self.con, state, vals)
        own, uni, ava = 0, 0, 0
        for row in data:
            own += row[5]
            ava += 1
            if row[5] >= 1:
                uni += 1
            items = {key: QTableWidgetItem(str(val)) for key, val in zip(self.header_labels, row)}
            self.table.insertRow(self.items)
            for i in range(len(list(items.keys()))):
                self.table.setItem(self.items, i, items[self.header_labels[i]])
            self.items += 1
        self.remove_select(var)
        self.table.setSortingEnabled(True)
        self.summary.setText(f'Owned: {own} \tUnique: {uni} \tAvailable: {ava}')

    def add_to_packs(self, resp=None):
        if not resp:
            resp = self.pack_list
        for elem in resp:
            self.pack_list_combo.addItem(
                f"{elem[1]} - {elem[0]} - ({elem[3]}) - [{elem[2]}]")
        self.pack_list_combo.setPlaceholderText(f"{str(self.pack_list_combo.count())} packs")
        self.pack_list_combo.setCurrentIndex(-1)

    def combo_set(self):
        """Method populates set_list_combo with sets in collection."""
        self.set_list_combo.blockSignals(True)
        self.set_list_combo.clear()
        for row in self.set_list:
            self.set_list_combo.addItem(f'{row[0]} - {row[1]} ({row[2]})')
        self.set_list_combo.setCurrentIndex(-1)
        self.set_list_combo.blockSignals(False)

    def clear_table(self, table):
        """Method empties tables."""
        table.clearContents()
        count = table.rowCount()
        for i in range(0, count+1):
            table.removeRow(count-i)


class Window(QMainWindow):
    def __init__(self, widget):
        super().__init__()
        self.setWindowTitle('Yu-Gi-Oh! Collection Manager')
        self.setGeometry(0, 0, 1920, 1080)
        self.setWindowState(Qt.WindowMaximized)

        # Menu
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu('File')

        exit_action = QAction('Exit', self)
        update_action = QAction('Update', self)

        exit_action.triggered.connect(self.exit_app)
        update_action.triggered.connect(self.update_db)

        for action in [exit_action, update_action]:
            self.file_menu.addAction(action)
        self.setCentralWidget(widget)

    @Slot()
    def exit_app(self):
        QApplication.quit()

    @Slot()
    def update_db(self):
        """Check for database updates"""
        version, date = select_row(widget.con, "select * from db_version;")
        url = "https://db.ygoprodeck.com/api/v7/checkDBVer.php"
        r = requests.get(url)
        old_date = datetime.date.fromisoformat(date)
        new_date = datetime.date.fromisoformat(r.json()[0]['last_update'].split()[0])
        new_vers = r.json()[0]['database_version']
        if old_date < new_date:
            ret = QMessageBox.question(self, "Update Database",
                                       f"""Database is on version {version}, last updated on {old_date}.
                                       \nVersion {new_vers} updated on {new_date} is available.\nUpdate database?""",
                                       buttons=QMessageBox.StandardButtons(QMessageBox.StandardButton.Yes
                                                                           | QMessageBox.StandardButton.No),
                                       defaultButton=QMessageBox.StandardButton.Yes)
        else:
            ret = QMessageBox.information(self, "Database up to date",
                                          f"""Database is on version {version}, last updated on {old_date}.
                                          \nYou are on the most recent update.""", QMessageBox.StandardButton.Ok)
        if ret == QMessageBox.StandardButton.Yes:
            update_tables(widget.con)


if __name__ == "__main__":
    import traceback
    import time
    try:
        print('Launching program...')
        tic = time.perf_counter()
        # Qt Application
        app = QApplication(sys.argv)
        # QWidget
        widget = Widget()
        # QMainWindow using QWidget as central widget
        window = Window(widget)
        window.show()
        toc = time.perf_counter()
        print(f'It took {toc-tic:.4f} seconds to open the window.')

        # with open(path('style.qss'), 'r') as f:
        with open(path('material.qss'), 'r') as f:
            _style = f.read()
            app.setStyleSheet(_style)
        # Execute application
        sys.exit(app.exec())
    except Exception as e:
        traceback.print_exc()
        print(f'An Error has occurred. {e} Let me know what it was.')
        input()