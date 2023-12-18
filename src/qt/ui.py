from modules.location_designation import path
from modules.collapse_widget import CollapsibleBox

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QComboBox, QFrame, QAbstractItemView, QHBoxLayout, QLabel,
                               QPushButton, QCheckBox, QVBoxLayout, QTableWidget,
                               QHeaderView, QGridLayout, QLineEdit)

class Ui_collector(object):
    def setupUI(self):
        # Window layout
        # Top
        top_layout = QHBoxLayout()
        filter_layout = QGridLayout()

        self.set_list_combo = QComboBox()
        self.set_list_combo.setPlaceholderText('')
        self.set_list_combo.setMaxVisibleItems(15)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Search')
        self.search_btn = QPushButton('Search')

        filter_labels = {label: QLabel(label) for label in ['Type', 'Race', 'Archetype', 'Attribute', 'Level/Rank', 'Link']}
        self.filter_combo = {label: QComboBox() for label in ['Type', 'Race', 'Archetype', 'Attribute', 'Level', 'Linkval']}
        for i in range(6):
            filter_layout.addWidget(filter_labels[list(filter_labels.keys())[i]], i % 3, 2 * (i // 3))
            filter_layout.addWidget(self.filter_combo[list(self.filter_combo.keys())[i]], i % 3, 2 * (i // 3) + 1)
        box = CollapsibleBox("Filter:")
        box.setContentLayout(filter_layout)

        self.reset_btn = QPushButton('Reset filter')
        self.owned_check = QCheckBox('Owned only')
        self.all_check = QCheckBox('All cards')

        top_layout.addWidget(self.set_list_combo)
        top_layout.addWidget(self.search_edit)
        top_layout.addWidget(self.search_btn)
        top_layout.addWidget(box)
        top_layout.addWidget(self.reset_btn)
        top_layout.addWidget(self.owned_check)
        top_layout.addWidget(self.all_check)

        # Left
        left_layout = QVBoxLayout()
        bot_layout = QHBoxLayout()
        but_layout = QVBoxLayout()
        sort_layout = QVBoxLayout()

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
        self.summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pack_list_combo = QComboBox()
        self.pack_list_combo.setMaxVisibleItems(20)
        self.main_sets_check = QCheckBox('Show only main sets', self)
        self.sort_sets_combo = QComboBox()
        for item in ['Sort By', 'Set Code', 'Date', 'Number of cards']:
            self.sort_sets_combo.addItem(item)
        self.sort_direction_combo = QComboBox()
        for item in ['Asc', 'Desc']:
            self.sort_direction_combo.addItem(item)
        self.view_set_btn = QPushButton('View set')
        self.add_set_btn = QPushButton('Add set to collection')

        bot_layout.addWidget(self.pack_list_combo)
        bot_layout.addWidget(self.main_sets_check)
        bot_layout.addLayout(sort_layout)
        sort_layout.addWidget(self.sort_sets_combo)
        sort_layout.addWidget(self.sort_direction_combo)
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
            self.labels[key].setTextFormat(Qt.RichText)
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
        self.owned_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bans_list = QTableWidget()
        self.bans_list.setColumnCount(2)
        self.bans_list.setHorizontalHeaderLabels(['Format', 'Banlist'])
        self.bans_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bans_list.verticalHeader().setVisible(False)
        self.bans_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.bans_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bans_list.setSortingEnabled(True)

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