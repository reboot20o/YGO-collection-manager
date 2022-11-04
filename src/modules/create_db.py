import sqlite3
from sqlite3 import Error
from urllib.request import pathname2url

def create_connection(db_file):
    con = None
    try:
        dburi = 'file:{}?mode=rw'.format(pathname2url(db_file))
        con = sqlite3.connect(db_file, uri=True)
    except sqlite3.OperationalError:
        con = sqlite3.connect(db_file)
        table_initialization(con)
    except Error as e:
        print(e)
    return con

def create_table(con, create_sql):
    try:
        cur = con.cursor()
        cur.execute(create_sql)
    except Error as e:
        print(e)

def insert_row(con, sql, card):
    try:
        cur = con.cursor()
        cur.execute(sql, card)
        con.commit()
    except Error as e:
        print(e)

def insert_rows(con, sql, cards):
    try:
        cur = con.cursor()
        cur.executemany(sql, cards)
        con.commit()
    except Error as e:
        print(e)

def select_row(con, sql, val=()):
    try:
        cur = con.cursor()
        return cur.execute(sql, val).fetchone()
    except Error as e:
        print(e)

def select_rows(con, sql, val=()):
    try:
        cur = con.cursor()
        return cur.execute(sql, val).fetchall()
    except Error as e:
        print(e)

def table_initialization(con):
    sql = ("""create table if not exists all_cards ( \
                id text,
                name text primary key,
                type text,
                descript text,
                race text,
                archetype text,
                atk int,
                def int,
                level int,
                attribute text,
                scale int,
                linkval int,
                tcg_date text,
                ocg_date text);""",
           """create table if not exists sets ( \
                id text,
                name text,
                set_code text,
                set_id text,
                set_rarity text,
                set_rarity_code text,
                constraint sets_FK foreign key (name) references all_cards(name));""",
           """create table if not exists banlist ( \
                id text,
                name text,
                tcg text,
                ocg text,
                goat text,
                constraint banlist_FK foreign key (name) references all_cards(name));""",
           """create table if not exists formats ( \
                name text,
                format text,
                constraint format_FK foreign key (name) references all_cards(name));""",
           """create table if not exists set_list ( \
                set_code text primary key,
                set_name text,
                size int,
                release text,
                subset text);""",
           """create table if not exists set_cards ( \
               id text,
               name text,
               set_code text,
               set_id text,
               set_rarity text,
               owned int,
               constraint set_cards_FK foreign key (name) references all_cards(name),
               constraint set_cards_FK_1 foreign key (set_code) references set_list(set_code));""",
           "create table if not exists db_version (version text, date text);",
           "create virtual table if not exists tri using fts5(name, archetype, tokenize='trigram');")
    if con is not None:
        for state in sql:
            create_table(con, state)