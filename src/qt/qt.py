import sys
import os
if not getattr(sys, 'frozen', False):
    if os.getcwd().__contains__('qt'):
        os.chdir('../../')
    sys.path.append('src')

from modules.create_db import create_connection, select_rows, select_row, insert_row, insert_rows
from modules.location_designation import path, asset_path
from modules.db_remove import get_set, update_tables
from modules.collapse_widget import CollapsibleBox

import requests
from PIL import Image
import json
import datetime

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QImage, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QAbstractItemView, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QCheckBox, QVBoxLayout, QWidget, QTableWidget,
                               QTableWidgetItem, QHeaderView, QGridLayout, QMessageBox, QScrollArea, QLineEdit,
                               QListWidget, QSpinBox)


class Widget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.items = 0
        self.detached = []
        db_loc = asset_path('cards.db')
        self.con, update = create_connection(db_loc)
        if update:
            update_tables(self.con)
        self.set_list = select_rows(self.con, "select set_code, set_name, release from set_list order by release asc;")

        # Top
        top_layout = QHBoxLayout()
        filter_layout = QGridLayout()

        content = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        box = CollapsibleBox("Filter:")
        self.set_list_combo = QComboBox()
        self.set_list_combo.setPlaceholderText('')
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Search')
        search_btn = QPushButton('Search')

        filter_labels = {label: QLabel(label) for label in ['Type', 'Race', 'Archetype', 'Attribute', 'Level/Rank', 'Link']}
        self.filter_combo = {label: QComboBox() for label in ['Type', 'Race', 'Archetype', 'Attribute', 'Level', 'Linkval']}
        for i in range(6):
            filter_layout.addWidget(filter_labels[list(filter_labels.keys())[i]], i % 3, 2 * (i // 3))
            filter_layout.addWidget(self.filter_combo[list(self.filter_combo.keys())[i]], i % 3, 2 * (i // 3) + 1)
        box.setContentLayout(filter_layout)

        reset_btn = QPushButton('Reset filter')
        self.owned_check = QCheckBox('Owned only')
        self.all_check = QCheckBox('All cards')

        top_layout.addWidget(self.set_list_combo)
        top_layout.addWidget(self.search_edit)
        top_layout.addWidget(search_btn)
        top_layout.addWidget(box)
        top_layout.addWidget(reset_btn)
        top_layout.addWidget(self.owned_check)
        top_layout.addWidget(self.all_check)

        # Left
        left_layout = QVBoxLayout()
        bot_layout = QHBoxLayout()
        but_layout = QVBoxLayout()

        self.header_labels = ['Id', 'Name', 'Type', 'Archetype', 'Race', 'Owned', 'Rarity', 'Set Code']
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(self.header_labels)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSortingEnabled(True)

        self.summary = QLabel('Owned: \t Unique: \t Available:', self)
        self.pack_list_combo = QComboBox()
        self.main_sets_check = QCheckBox('Show only main sets', self)
        self.view_set_btn = QPushButton('View set')
        self.add_set_btn = QPushButton('Add set to collection')

        bot_layout.addWidget(self.pack_list_combo)
        bot_layout.addWidget(self.main_sets_check)
        bot_layout.addLayout(but_layout)
        but_layout.addWidget(self.view_set_btn)
        but_layout.addWidget(self.add_set_btn)
        left_layout.addWidget(self.table)
        left_layout.addWidget(self.summary)
        left_layout.addLayout(bot_layout)

        # Right
        label_layout = QGridLayout()
        btm_layout = QVBoxLayout()
        self.tags = ['image', 'description', 'name', 'type', 'attribute', 'race', 'level/rank', 'attack', 'defense',
                     'archetype', 'link rating', 'scale']
        self.labels = {tag: QLabel(tag.title(), self) for tag in self.tags}
        for key in self.tags:
            self.labels[key].setFrameStyle(QFrame.Panel | QFrame.Sunken)
            self.labels[key].setLineWidth(2)
            if key not in ('image', 'name', 'description'):
                self.labels[key].setFixedSize(200, 80)
                self.labels[key].setWordWrap(True)
            elif key == 'description':
                self.labels[key].setWordWrap(True)
            elif key == 'name':
                self.labels[key].setFixedSize(600, 80)
        self.im = QImage(path(f'images/Yugioh_Card_Back.jpg'))
        self.labels['image'].setPixmap(QPixmap(self.im))

        self.owned_label = QLabel()
        self.bans_list = QListWidget()
        self.edit_owned_btn = QPushButton('Submit Changes')
        self.cardsets_table = QTableWidget()
        self.cardsets_table.setColumnCount(3)
        self.cardsets_table.setHorizontalHeaderLabels(['Sets', 'Rarity', '# Owned'])
        self.cardsets_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cardsets_table.verticalHeader().setVisible(False)
        self.cardsets_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cardsets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cardsets_table.setSortingEnabled(True)

        label_layout.addWidget(self.labels['image'], 0, 0, 4, 1)
        label_layout.addWidget(self.labels['name'], 0, 1, 1, 3)
        label_layout.addWidget(self.labels['description'], 4, 1, 1, 3)
        for i in range(3, len(self.tags)):
            label_layout.addWidget(self.labels[self.tags[i]], i // 3, (i - 3) % 3 + 1)
        label_layout.addLayout(btm_layout, 4, 0)

        btm_layout.addWidget(self.owned_label)
        btm_layout.addWidget(self.cardsets_table)
        btm_layout.addWidget(self.edit_owned_btn)
        btm_layout.addWidget(self.bans_list)

        # Main layout
        main_layout = QVBoxLayout()
        layout = QHBoxLayout()
        layout.addLayout(left_layout, 1)
        layout.addLayout(label_layout, 1)
        main_layout.addLayout(top_layout)
        main_layout.addLayout(layout)

        self.setLayout(main_layout)

        self.pop_set_list()
        self.combo_set()
        self.reset_filter()

        # Signals and slots
        self.set_list_combo.currentTextChanged.connect(self.set_table)
        self.search_edit.returnPressed.connect(self.search)
        search_btn.clicked.connect(self.search)
        for key in self.filter_combo:
            self.filter_combo[key].activated.connect(self.set_filter)
        reset_btn.clicked.connect(self.reset_filter)
        self.all_check.toggled.connect(self.select_all)
        self.owned_check.toggled.connect(self.remove_select)
        self.table.itemSelectionChanged.connect(self.select_item)
        self.view_set_btn.clicked.connect(self.view_set)
        self.add_set_btn.clicked.connect(self.add_set)
        self.main_sets_check.toggled.connect(self.pop_set_list)
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
        self.bans_list.clear()
        row = self.table.currentIndex().row()
        card_id = self.table.item(row, 0).text()
        info = select_row(self.con, """select a.descript, a.name, a.type, a.attribute, a.race, a.level, a.atk, a.def, 
                                    a.archetype, a.linkval, a.scale, sum(coalesce(s.owned, 0)) as owned  
                                    from all_cards as a left join set_cards as s on a.name=s.name where a.id=?
                                    group by a.name, a.type, a.attribute, a.race, a.archetype, a.level, a.atk, a.def, 
                                    a.linkval, a.scale, a.descript;""", (card_id,))
        sets = select_rows(self.con, """select s.set_id, s.set_rarity_code, coalesce(sc.owned,0) from sets as s 
                                        left join set_cards as sc on s.set_id=sc.set_id where s.id=?""", (card_id,))
        bans = select_row(self.con, "select tcg, ocg, goat from banlist where id=?", (card_id,))
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
            self.labels[key].setText(f'{key.title()}:\n{val}')
        self.owned_label.setText(f'Owned:\n{info[-1]}')
        for i in range(len(sets)):
            self.cardsets_table.insertRow(i)
            items = [QTableWidgetItem(str(val)) for val in sets[i]]
            self.cardsets_table.setCellWidget(i, 2, QSpinBox())
            self.cardsets_table.cellWidget(i, 2).setValue(sets[i][2])
            self.cardsets_table.cellWidget(i, 2).setMaximum(10000)
            for j in range(2):
                self.cardsets_table.setItem(i, j, items[j])
        self.bans_list.addItems(
            [f"{key} - {value}" for key, value in zip(['TCG', 'OCG', 'GOAT'], bans) if value is not None])

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
    def pop_set_list(self):
        """Slot for main_sets_check. Populates pack_list_combo with sets not in collection."""
        self.pack_list_combo.clear()
        sets = {elem[0]: elem[1] for elem in self.set_list}
        with open(asset_path('set_list.json'), 'r') as f:
            resp = json.loads(f.read())
        resp[:] = [elem for elem in resp if
                   (elem['set_code'] not in sets.keys() and elem['set_name'] not in sets.values())]
        check = ['special', 'participation', 'promotion', 'subscription', 'prize']
        if self.main_sets_check.isChecked():
            resp[:] = [elem for elem in resp if not any(map(elem['set_name'].lower().__contains__, check))]
        resp = sorted(resp, key=lambda e: (e['set_code'], e['set_name']))
        for elem in resp:
            if 'tcg_date' in elem.keys():
                self.pack_list_combo.addItem(
                    f"{elem['set_code']} - {elem['set_name']} - ({elem['tcg_date']}) [{elem['num_of_cards']}]")
        self.pack_list_combo.setPlaceholderText(str(self.pack_list_combo.count()))
        self.pack_list_combo.setCurrentIndex(-1)

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
        with open(asset_path('set_list.json'), 'r') as f:
            resp = json.loads(f.read())
        for key, val in owned.items():
            if key in list(check.keys()) and val != check[key]:
                to_add.append((val, key))
                print(f'The value for {key} changed from {check[key]} to {val}')
            elif key not in list(check.keys()) and val > 0:
                code = key.split('-')[0]
                for row in resp:
                    if 'tcg_date' in row.keys() and row['set_code'] == code:
                        text = f"{row['set_code']} - {row['set_name']} - ({row['tcg_date']}) [{row['num_of_cards']}]"
                        break
                self.add_to_database(text)
                to_add.append((val, key))
                print(f'Set {key} not in database, but owned is {val}')
        insert_rows(self.con, "update set_cards set owned = ? where set_id = ?", to_add)
        self.select_item()

    def add_to_database(self, text):
        """Method adds set and set cards to database."""
        pack, cards = get_set(text)
        insert_row(self.con, "insert into set_list values (?,?,?,?,?)", pack)
        insert_rows(self.con, "insert or ignore into set_cards values (?,?,?,?,?,?)", cards)

        self.set_list = select_rows(self.con, "select set_code, set_name, release from set_list order by release asc;")
        self.pop_set_list()
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

        with open(path('style.qss'), 'r') as f:
            _style = f.read()
            app.setStyleSheet(_style)
        # Execute application
        sys.exit(app.exec())
    except Exception:
        traceback.print_exc()
        print('An Error has occurred. Let me know what it was.')
        input()