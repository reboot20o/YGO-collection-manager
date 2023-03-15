from modules.create_db import create_connection, insert_row, select_rows, select_row, insert_rows
from modules.db_remove import update_tables
from modules.location_designation import path
from modules.display_res import scaled
import pandas as pd
import requests
import datetime
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter.messagebox import askyesno, showinfo
from sys import platform

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        db_loc = path('cards.db')
        self.con = create_connection(db_loc)
        self.set_list = select_rows(self.con, "select set_code, set_name, release from set_list order by release asc;")
        self.make_window()

    def make_menu(self):
        """Initialize menubar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        option_menu = tk.Menu(menubar, tearoff=0)
        option_menu.add_command(label='Re-populate database', command=lambda: update_tables(self.con))
        option_menu.add_command(label='Check for updates', command=self.update_db)
        option_menu.add_command(label="Reload", command=self.reload)
        menubar.add_cascade(label='Options', menu=option_menu)

    def make_frames(self):
        """Create main window containers"""
        # Create main containers
        self.top_frame = ttk.Frame(self)
        self.btm_frame = ttk.Frame(self)
        self.left_frame = ttk.Frame(self.btm_frame, width=scaled(875))
        # self.left_frame = ttk.Frame(self.btm_frame)
        self.summary_frame = ttk.Frame(self.left_frame)
        self.right_frame = ttk.Frame(self.btm_frame, width=scaled(1020))
        # self.right_frame = ttk.Frame(self.btm_frame)
        self.view_frame = ttk.Frame(self.right_frame)
        self.edit_frame = ttk.Frame(self.right_frame)

        # Layout containers
        # self.grid_rowconfigure(0, weight=1)
        # self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        # self.top_frame.grid_rowconfigure(0, weight=1)
        self.btm_frame.grid_rowconfigure(0, weight=1)
        # self.btm_frame.grid_columnconfigure(0, weight=1)
        # self.btm_frame.grid_columnconfigure(1, weight=1)
        # self.left_frame.grid_propagate(0)
        # self.right_frame.grid_propagate(0)

        self.top_frame.grid(row=0, sticky='ew')
        self.btm_frame.grid(row=1, sticky='nsew')
        self.left_frame.grid(row=0, column=0, sticky='nsew')
        self.summary_frame.grid(row=1, column=0, sticky='nsew')
        self.right_frame.grid(row=0, column=1, sticky='ns')
        self.view_frame.grid(row=0, sticky='nsew')
        self.edit_frame.grid(row=1, sticky='nsew')

    def make_widgets(self):
        """Create widgets and initialize in respective containers"""
        # Styles
        s = ttk.Style()
        s.configure('Effect.TLabel', background='#5a66a5', foreground='white', font=('Times', 12), justify=tk.LEFT,
                    padding=10, width=18)
        s.configure('Des.TLabel', font=('Calibri', 12), justify=tk.LEFT,
                    padding=10, width=72, anchor=tk.NW)
        s.configure('Box.TLabel', background='#5a66a5', foreground='white', font=('Arial', 12), justify=tk.LEFT,
                    padding=5, width=10)
        args = {'padx': 5, 'pady': 5, 'ipadx': 0, 'ipady': 0}

        # Create widgets for top_frame
        ttk.Label(self.top_frame, text='Set:').grid(row=0, column=0, **args)
        ttk.Label(self.top_frame, text='Filter by:').grid(row=0, column=1, **args)

        self.set_var = tk.StringVar()
        self.set_obj = ttk.Combobox(self.top_frame, textvariable=self.set_var, height=35,
                                    values=[f'{elem[0]} - {elem[1]} ({elem[2]})' for elem in self.set_list],
                                    state='readonly')
        self.set_obj.grid(row=1, column=0, **args)
        self.set_obj.bind('<<ComboboxSelected>>', self.items_select)
        try:
            self.set_obj['width'] = len(max(self.set_obj['values'], key=len))
        except ValueError:
            self.set_obj['width'] = 50

        self.combo_var = tk.StringVar()
        self.combo = ttk.OptionMenu(self.top_frame, self.combo_var, 'Type', *['Type', 'Attribute', 'Race', 'Archetype'],
                                    command=self.filter_change)
        self.combo.grid(row=1, column=1, **args)

        self.filter_var = tk.StringVar()
        self.filt = ttk.Combobox(self.top_frame, textvariable=self.filter_var, height=35, state='readonly')
        self.filt.grid(row=1, column=2, **args)

        self.check_var = tk.IntVar()
        ttk.Checkbutton(self.top_frame, text='Owned', variable=self.check_var, onvalue=1, offvalue=0,
                        command=self.check_select).grid(row=1, column=3, **args)

        self.all_var = tk.IntVar()
        ttk.Checkbutton(self.top_frame, text='All cards', variable=self.all_var, onvalue=1, offvalue=0,
                        command=self.all_select).grid(row=1, column=4, **args)

        ttk.Label(self.top_frame, text='Search by card or archetype').grid(row=0, column=5, **args)

        self.search_var = tk.StringVar()
        self.search_bar = ttk.Entry(self.top_frame, textvariable=self.search_var, width=100)
        self.search_bar.grid(row=1, column=5, sticky='ew', **args)
        self.search_bar.bind('<KeyRelease-Return>', self.search)

        ttk.Button(self.top_frame, text='Search', command=self.search).grid(row=1, column=6, **args)

        # Create widgets for left_frame
        columns = ('id', 'name', 'type', 'archetype', 'race', 'owned', 'rarity', 'set code')
        col_dict = {'id': 65, 'type': 180, 'archetype': 110, 'race': 85, 'owned': 32, 'rarity': 60, 'set code': 90}
        self.tree = ttk.Treeview(self.left_frame, columns=columns, height=40, show='headings')
        for col in columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self.treeview_sort_columns(self.tree, _col, False))
        scrollbar_tree = ttk.Scrollbar(self.left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar_tree.set)
        for col in col_dict.keys():
            self.tree.column(col, width=col_dict[col])
        self.tree.grid(row=0, column=0, sticky='nsw', **args)
        scrollbar_tree.grid(row=0, column=1, sticky='ns')
        self.tree.bind('<<TreeviewSelect>>', self.tree_select)

        # Create widgets for summary_frame
        self.summary_var = tk.StringVar(value='Owned: \t-\tUnique: \t-\tAvailable: ')
        ttk.Label(self.summary_frame, textvariable=self.summary_var).grid(row=0, column=0, columnspan=2, **args)

        self.misc_var = tk.IntVar()
        ttk.Checkbutton(self.summary_frame, text='Show only main sets', variable=self.misc_var,
                        command=self.pop_set_list).grid(row=1, column=1, **args)

        self.set_combo_var = tk.StringVar()
        self.set_combo = ttk.Combobox(self.summary_frame, textvariable=self.set_combo_var, height=20)
        self.pop_set_list()
        self.set_combo.grid(row=1, column=0, **args)

        ttk.Button(self.summary_frame, text='Add set to collection',
                   command=self.add_collection).grid(row=2, column=1)
        ttk.Button(self.summary_frame, text='View set',
                   command=self.view_set).grid(row=0, column=1)

        # Create widgets for right_frame
        # view_frame
        self.img = ImageTk.PhotoImage(file=path('images/Yugioh_Card_Back.jpg'), name='card_back')
        self.image_label = ttk.Label(self.view_frame, image='card_back')
        self.image_label.grid(row=1, rowspan=3, column=0, sticky='nw')

        self.name_var = tk.StringVar(value='Name')
        self.name = ttk.Label(self.view_frame, textvariable=self.name_var, font=('Helvetica', '24'),
                              background='#000000',
                              foreground='#fff', relief='groove', justify=tk.CENTER, anchor=tk.CENTER)
        self.name.grid(row=0, column=0, columnspan=5, sticky='nwe')

        self.type_var = tk.StringVar(value='Type')
        self.type = ttk.Label(self.view_frame, textvariable=self.type_var, style='Effect.TLabel', wraplength=150)
        self.type.grid(row=1, column=1, sticky='nswe', **args)

        self.attr_var = tk.StringVar(value='Attribute')
        self.attr = ttk.Label(self.view_frame, textvariable=self.attr_var, style='Effect.TLabel')
        self.attr.grid(row=1, column=2, sticky='nswe', **args)

        self.race_var = tk.StringVar(value='Race')
        self.race = ttk.Label(self.view_frame, textvariable=self.race_var, style='Effect.TLabel')
        self.race.grid(row=1, column=3, sticky='nswe', **args)

        self.arche_var = tk.StringVar(value='Archetype')
        self.arche = ttk.Label(self.view_frame, textvariable=self.arche_var, style='Effect.TLabel', wraplength=100)
        self.arche.grid(row=1, column=4, sticky='nswe', **args)

        self.lvl_var = tk.StringVar(value='Level/Rank')
        self.lvl = ttk.Label(self.view_frame, textvariable=self.lvl_var, style='Effect.TLabel')
        self.lvl.grid(row=2, column=1, sticky='nswe', **args)

        self.atk_var = tk.StringVar(value='Atk')
        self.atk = ttk.Label(self.view_frame, textvariable=self.atk_var, style='Effect.TLabel')
        self.atk.grid(row=2, column=2, sticky='nsew', **args)

        self.defe_var = tk.StringVar(value='Def')
        self.defe = ttk.Label(self.view_frame, textvariable=self.defe_var, style='Effect.TLabel')
        self.defe.grid(row=2, column=3, sticky='nsew', **args)

        self.link_var = tk.StringVar(value='Link Value')
        self.link = ttk.Label(self.view_frame, textvariable=self.link_var, style='Effect.TLabel')
        self.link.grid(row=2, column=4, sticky='nsew', **args)

        self.scale_var = tk.StringVar(value='Scale')
        self.scale = ttk.Label(self.view_frame, textvariable=self.scale_var, style='Effect.TLabel')
        self.scale.grid(row=3, column=1, sticky='nsew', **args)

        self.own_var = tk.StringVar(value='Number Owned')
        self.owned = ttk.Label(self.view_frame, textvariable=self.own_var)
        self.owned.grid(row=4, column=0, sticky='nsew', **args)

        self.set_list_var = tk.Variable()
        self.set_listing = tk.Listbox(self.view_frame, listvariable=self.set_list_var, height=5)
        self.set_listing.grid(row=5, column=0, sticky='nsew', **args)

        self.ban_var = tk.Variable()
        self.ban_list = tk.Listbox(self.view_frame, listvariable=self.ban_var, height=3)
        self.ban_list.grid(row=6, column=0, sticky='nsew', **args)

        self.des_var = tk.StringVar(value='Card Text')
        self.des = ttk.Label(self.view_frame, textvariable=self.des_var, style='Des.TLabel', wraplength=675)
        self.des.grid(row=3, column=1, columnspan=4, rowspan=4, sticky='nsew', **args)

        # edit_frame
        ttk.Label(self.edit_frame, text='Owned:', style='Box.TLabel').grid(row=0, column=1, **args)

        self.owned_edit_var = tk.StringVar()
        self.own_edit = ttk.Spinbox(self.edit_frame, from_=0, to=100000, textvariable=self.owned_edit_var)
        self.own_edit.grid(row=1, column=1, **args)

        ttk.Button(self.edit_frame, text='Save edits', command=self.save_changes).grid(row=2, column=3, **args)

    def make_window(self):
        # Initialize window
        self.title('Yu-Gi-Oh! Card Database Viewer')
        # self.iconbitmap(path('images/yugioh.ico'))
        self.tk.call('tk', 'scaling', 1)
        self.geometry(f'{scaled(1920)}x{scaled(1080)}')
        # self.geometry(f'{1920}x{1080}')
        self.resizable(True, True)
        self.make_frames()
        self.make_menu()
        self.make_widgets()

    def reload(self):
        self.destroy()
        self.__init__()

    def get_set(self):
        var = self.set_combo_var.get()
        pack_code, pack = var.split(' - ')[0:2]
        release = [int(date) for date in var.split(' - ')[2].split()[0][1:-1].split('-')]
        pack_date = datetime.date(release[0], release[1], release[2])
        pack_size = var.split(' - ')[2].split()[1][1:-1]
        URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php?cardset=" + pack.replace(" ", "%20")
        r = requests.get(URL)
        df = pd.DataFrame(r.json()["data"])
        codes = []
        rarity = []
        for card in df['card_sets']:
            try:
                codes.append(next((item['set_code'] for item in card if item["set_name"].endswith(pack)), "Err"))
            except TypeError:
                codes.append("Err")
            try:
                rarity.append(
                    next((item['set_rarity_code'] for item in card if item["set_name"].endswith(pack)), "Err"))
            except TypeError:
                rarity.append("Err")

        setCodes = pd.Series(codes, name='set_code')
        setRarity = pd.Series(rarity, name='rarity')
        ind, cols = pd.factorize(df['id'])
        for card in df['id']:
            col = cols.get_loc(card)
            df.at[col, 'id'] = str(card).zfill(8)

        cols = df.columns.tolist()
        cols.remove("name")
        cols.remove("id")

        df = df.drop(columns=cols)
        df = pd.concat([df, setCodes, setRarity], axis=1)
        df = df[["id", "set_code", "name", "rarity"]]
        df = df.sort_values(by='set_code').reset_index(drop=True)

        if df[df.duplicated(subset=['set_code'])].size > 0:
            for i in df[df.duplicated(subset=['set_code'])].index:
                temp = df.loc[i, 'set_code']
                df.loc[i, 'set_code'] = temp[:-3] + str(int(temp[-3:])+1).zfill(3)

        set_list = df.to_numpy()
        cards = []
        for elem in set_list:
            id = elem[0]
            set_code = elem[1]
            name = elem[2]
            rarity = elem[3]
            cards.append((id, name, pack_code, set_code, rarity, 0))

        return [(pack_code, pack, pack_size, pack_date, None), cards]

    def view_set(self):
        pack, cards = self.get_set()
        state = """select a.id, a.name, a.type, a.archetype, a.race, coalesce(ss.owned,0) as owned, s.set_rarity_code, s.set_id
                            from all_cards as a left join sets as s on a.name=s.name
                            left outer join set_cards as ss on s.set_id=ss.set_id
                            where s.set_code=?
                            order by s.set_id;"""
        self.empty_tree()
        self.add_tree(state, (pack[0],))

    def add_collection(self):
        """Add the selected set to collection and update the drop-down to reflect change"""
        pack, cards = self.get_set()
        insert_row(self.con, "insert into set_list values (?,?,?,?,?)", pack)
        insert_rows(self.con, "insert or ignore into set_cards values (?,?,?,?,?,?)", cards)

        showinfo(message=f'The set {pack[1]} has been added to the collection!')
        self.set_list = select_rows(self.con, "select set_code, set_name, release from set_list order by release asc;")
        self.pop_set_list()
        self.set_obj['values'] = [f'{elem[0]} - {elem[1]} ({elem[2].split("-")[0]})' for elem in self.set_list]
        self.set_obj['width'] = len(max(self.set_obj['values'], key=len))

    def update_db(self):
        """Check for database updates"""
        version, date = select_row(self.con, "select * from db_version;")
        url = "https://db.ygoprodeck.com/api/v7/checkDBVer.php"
        r = requests.get(url)
        old_date = datetime.date.fromisoformat(date)
        new_date = datetime.date.fromisoformat(r.json()[0]['last_update'].split()[0])
        new_vers = r.json()[0]['database_version']
        ask = False
        if old_date < new_date:
            ask = askyesno(message=f"Database is on version {version}, last updated on {old_date}.\nVersion {new_vers} updated on {new_date} is available.\nUpdate database?")
        else:
            showinfo(message=f"Database is on version {version}, last updated on {old_date}.\nYou are on the most recent update.")
        if ask:
            update_tables(self.con)

    def pop_set_list(self):
        """Populate the set_list table with cards from sets added to collection"""
        check_val = self.misc_var.get()
        sets = {elem[0]: elem[1] for elem in self.set_list}
        # set_codes = [item[0] for item in self.set_list]
        with open(path('set_list.json'), 'r') as f:
            resp = json.loads(f.read())
        resp[:] = [elem for elem in resp if (elem['set_code'] not in sets.keys() and elem['set_name'] not in sets.values())]
        check = ['special', 'participation', 'promotion', 'subscription', 'prize']
        if check_val == 1:
            resp[:] = [elem for elem in resp if not any(map(elem['set_name'].lower().__contains__, check))]
        resp = sorted(resp, key=lambda e: (e['set_code'], e['set_name']))
        vals = [f"{elem['set_code']} - {elem['set_name']} - ({elem['tcg_date']}) [{elem['num_of_cards']}]"
                for elem in resp if 'tcg_date' in elem.keys()]
        self.set_combo['values'] = vals
        self.set_combo_var.set(f'{len(resp)}')
        self.set_combo['width'] = len(max(self.set_combo['values'], key=len))

    # Todo: Change number in entry to reflect number owned
    def save_changes(self):
        """Save edited value of owned"""
        name = self.name_var.get()
        own = self.owned_edit_var.get()
        tree_vals = self.tree.item(self.tree.focus())['values']
        card_id = str(tree_vals[0]).zfill(8)
        og, set_rarity, set_id = tree_vals[-3:]
        if not set_id:
            try:
                set_id, set_rarity = self.set_listing.get(self.set_listing.curselection()).split()
            except:
                showinfo(message="Select the set code of the card to be added!")
                return
        set_code = set_id.split('-')[0]
        change = {'id': card_id, 'name': name, 'set_code': set_code, 'set_id': set_id,
                  'set_rarity': set_rarity, 'own': own}
        state = """insert into set_cards values (:id, :name, :set_code, :set_id, :set_rarity, :own) on conflict(set_id) 
                    do update set owned=excluded.owned;"""
        if own == og or not own:
            showinfo(message="You didn't submit any changes!")
        else:
            insert_row(self.con, state, change)
            self.empty_tree()
            ment = """select a.id, a.name, a.type, a.archetype, a.race, s.owned, s.set_rarity, s.set_id
                    from all_cards as a
                    left join set_cards as s on a.name=s.name
                    where s.set_code=?
                    order by s.set_id;"""
            self.add_tree(ment, (change['set_code'],))

    def search(self, event=None):
        """Fuzzy search"""
        var = self.search_var.get()
        state = """select a.id, a.name, a.type, a.archetype, a.race, sum(coalesce(s.owned, 0)) as owned
                    from all_cards as a left join set_cards as s on a.name=s.name
                    inner join tri(?) as t on a.name=t.name
                    group by a.id, a.name, a.type, a.archetype, a.race
                    order by owned desc nulls last;"""
        self.empty_tree()
        self.add_tree(state, (var,))
        print(self.focus_get())

    def all_select(self):
        """View every card"""
        check_var = self.all_var.get()
        self.empty_tree()
        if check_var == 1:
            state = """select a.id, a.name, a.type, a.archetype, a.race, sum(coalesce(s.owned, 0)) as owned 
                    from all_cards as a left join set_cards as s on a.name=s.name 
                    group by a.id, a.name, a.type, a.archetype, a.race
                    order by owned desc nulls last;"""
            self.add_tree(state)
        else:
            self.set_var.set('')
            self.summary_var.set('Owned: \t-\tUnique: \t-\tAvailable: ')

    def check_select(self):
        var = self.check_var.get()
        self.remove_select(var)

    def remove_select(self, var):
        """Remove cards from tree view"""
        if var == 1:
            rows = self.tree.get_children()
            tree_row = [(row, self.tree.index(row)) for row in rows]
            for row in tree_row:
                if int(self.tree.set(row[0], column='owned')) == 0:
                    self.detached.append((row[0], row[1]))
                    self.tree.detach(row[0])
        if var == 0:
            for item in self.detached:
                self.tree.move(item[0], '', item[1])

    def tree_select(self, event):
        if self.focus_get() == self.tree:
            item = self.tree.focus()
            self.detail_view(self.tree.item(item, 'text'))

    def items_select(self, event):
        """Populate tree view with cards from selected set"""
        selected_set = self.set_obj.get().split(' - ')[0]
        state = """select a.id, a.name, a.type, a.archetype, a.race, s.owned, s.set_rarity, s.set_id
                    from all_cards as a
                    left join set_cards as s on a.name=s.name
                    where s.set_code=?
                    order by s.set_id;"""
        self.empty_tree()
        self.add_tree(state, (selected_set,))
        self.filter_var.set('')
        self.combo_var.set('')

    def detail_view(self, card_id):
        """Get info for card with card_id"""
        cur = self.con.cursor()
        card = select_row(self.con, """select a.name, a.type, a.attribute, a.race, a.archetype, a.level, a.atk, a.def, 
                        a.linkval, a.scale, sum(coalesce(s.owned, 0)) as owned, a.descript 
                        from all_cards as a left join set_cards as s on a.name=s.name where a.id=?
                        group by a.name, a.type, a.attribute, a.race, a.archetype, a.level, a.atk, a.def, a.linkval, 
                        a.scale, a.descript;""", (card_id,))
        sets = select_rows(self.con, "select set_code, set_id, set_rarity_code from sets where id=?", (card_id,))
        bans = select_row(self.con, "select tcg, ocg, goat from banlist where id=?", (card_id,))
        card_id = card_id.lstrip('0')
        size = 260,379
        try:
            self.im = ImageTk.PhotoImage(file=path(f'images/{card_id}.thumbnail'))
        except FileNotFoundError:
            url = f"https://images.ygoprodeck.com/images/cards/{card_id}.jpg"
            im = Image.open(requests.get(url, stream=True).raw)
            im.save(path(f'images/{card_id}.jpg'))
            im.thumbnail(size)
            im.save(path(f'images/{card_id}.thumbnail'), 'JPEG')
            self.im = ImageTk.PhotoImage(im)
        self.image_label['image'] = self.im
        self.add_detail(card, sets, bans)

    def add_detail(self, card, sets, bans):
        """Add card info the detail card view"""
        self.name_var.set(card[0])
        self.type_var.set(f'Type\n{card[1]}')
        self.attr_var.set(f'Attribute\n{card[2]}')
        self.race_var.set(f'Race\n{card[3]}')
        self.arche_var.set(f'Archetype\n{card[4]}')
        self.lvl_var.set(f'Level/Rank\n{card[5]}')
        self.atk_var.set(f'Atk\n{card[6]}')
        self.defe_var.set(f'Def\n{card[7]}')
        self.link_var.set(f'Link Value\n{card[8]}')
        self.scale_var.set(f'Scale\n{card[9]}')
        self.own_var.set(f'Owned\n{card[10]}')
        self.des_var.set(f'Card text\n{card[11]}')
        setlist = [f"{elem[1]} {elem[2]}" for elem in sets]
        self.set_list_var.set(setlist)
        banlist = [f"{key} - {value}" for key, value in zip(['TCG', 'OCG', 'GOAT'], bans[2:]) if value is not None]
        self.ban_var.set(banlist)

        args = {'padx': 5, 'pady': 5, 'ipadx': 0, 'ipady': 0}
        if card[1].endswith('Card'):
            self.spell_grid(args)
        elif card[1].startswith('Link'):
            self.link_grid(args)
        elif 'Pendulum' in card[1]:
            self.pend_grid(args)
        else:
            self.forget_grid()
            self.lvl.grid_configure(row=2, column=1, sticky='nsew', **args)
            self.atk.grid_configure(row=2, column=2, sticky='nsew', **args)
            self.defe.grid_configure(row=2, column=3, sticky='nsew', **args)
            self.des.grid_configure(row=3, column=1, rowspan=4, columnspan=4, sticky='nsew', **args)

    def forget_grid(self):
        """Forget select widgets in detail view"""
        self.link.grid_forget()
        self.scale.grid_forget()
        self.lvl.grid_forget()
        self.atk.grid_forget()
        self.defe.grid_forget()
        self.des.grid_forget()

    def pend_grid(self, args):
        """Detail card view for pendulum cards"""
        self.forget_grid()
        self.lvl.grid_configure(row=2, column=1, sticky='nsew', **args)
        self.atk.grid_configure(row=2, column=2, sticky='nsew', **args)
        self.defe.grid_configure(row=2, column=3, sticky='nsew', **args)
        self.scale.grid_configure(row=2, column=4, sticky='nsew', **args)
        self.des.grid_configure(row=3, column=1, rowspan=4, columnspan=4, sticky='nsew', **args)

    def link_grid(self, args):
        """Detail card view for link cards"""
        self.forget_grid()
        self.link.grid_configure(row=2, column=1, sticky='nsew', **args)
        self.atk.grid_configure(row=2, column=2, sticky='nsew', **args)
        self.des.grid_configure(row=3, column=1, rowspan=4, columnspan=4, sticky='nsew', **args)

    def spell_grid(self, args):
        """Detail card view for non monster cards"""
        self.forget_grid()
        self.des.grid_configure(row=2, column=1, rowspan=4, columnspan=4, sticky='nsew', **args)

    def add_tree(self, state, val=(), cards=None):
        """Add rows to tree view"""
        if cards:
            rows = cards
        else:
            rows = select_rows(self.con, state, val)
        self.detached = []
        var = self.check_var.get()
        own, unique, in_set = 0, 0, 0
        for row in rows:
            try:
                self.tree.insert('', tk.END, values=(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]),
                                 text=row[0])
            except IndexError:
                self.tree.insert('', tk.END, values=(row[0], row[1], row[2], row[3], row[4], row[5], "", ""),
                                 text=row[0])
            own += row[5]
            in_set += 1
            if row[5]>0:
                unique += 1
        self.remove_select(var)
        self.summary_var.set('Owned: {own:,}\tUnique: {unique:,}\tAvailable: {in_set:,}'.format(own=own, unique=unique,
                                                                                                in_set=in_set))

    def empty_tree(self):
        """Empty tree view"""
        for row in self.tree.get_children():
            self.tree.delete(row)

    def treeview_sort_columns(self, tv, col, reverse):
        """Click on tree view headers to sort columns"""
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)
        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        # reverse sort next time
        tv.heading(col, command=lambda: self.treeview_sort_columns(tv, col, not reverse))

    def filter_change(self, event):
        """Change the filter criteria and populate the corresponding filters"""
        label = self.combo_var.get().lower()
        vals = select_rows(self.con, """select count({field}), {field} from all_cards where {field} is not null \
        group by {field} order by {field}""".format(field=label))
        self.filt['values'] = [f'{str(elem[0])} - {elem[1]}' for elem in vals]
        self.filt['width'] = len(max(self.filt['values'], key=len))
        self.filt.bind('<<ComboboxSelected>>', self.filt_select)

    def filt_select(self, event):
        """Filter the tree view by the selected filter"""
        var = self.filter_var.get().split(' - ')[1]
        state = """select a.id, a.name, a.type, a.archetype, a.race, sum(coalesce(s.owned, 0)) as owned 
                    from all_cards as a left join set_cards as s on a.name=s.name 
                    where {field} = ?
                    group by a.id, a.name, a.type, a.archetype, a.race
                    order by owned desc nulls last;"""
        self.combo_dict = {"Type": state.format(field='type'),
                           "Archetype": state.format(field='archetype'),
                           "Race": state.format(field='race'),
                           "Attribute": state.format(field='attribute')}
        self.empty_tree()
        self.add_tree(self.combo_dict.get(self.combo_var.get()), (var,))
        self.set_var.set('')

def main():
    app = App()
    if platform == 'win32':
        app.state('zoomed')
    else:
        app.wm_attributes('-zoomed', 1)
    app.mainloop()

main()