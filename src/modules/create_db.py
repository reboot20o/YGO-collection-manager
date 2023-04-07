import sqlite3
from sqlite3 import Error
from urllib.request import pathname2url
from modules.location_designation import path
import time


def create_connection(db_file):
    """Method connects to database if it exists or creates it if it doesn't."""

    con = None
    update = False
    try:
        tic = time.perf_counter()
        dburi = 'file:{}?mode=rw'.format(pathname2url(db_file))
        con = sqlite3.connect(dburi, uri=True)
        toc = time.perf_counter()
        print(f'Successfully connected to database. It took {toc - tic:0.4f} seconds.')
    except sqlite3.OperationalError:
        con = sqlite3.connect(db_file)
        print('Created database. Now creating tables...')
        tic = time.perf_counter()
        table_initialization(con)
        toc = time.perf_counter()
        print(f'Done! It took {toc-tic:0.4f} seconds.')
        update = True
    except Error as e:
        print(e)
    return con, update

def create_table(con, create_sql):
    """Method executes query create_sql. Intended for table creation."""

    try:
        cur = con.cursor()
        cur.execute(create_sql)
    except Error as e:
        print(e)

def insert_row(con, sql, card):
    """Method inserts single row card into table detailed by query sql."""

    try:
        cur = con.cursor()
        cur.execute(sql, card)
        con.commit()
    except Error as e:
        print(e)

def insert_rows(con, sql, cards):
    """Same as method insert_row, but instead inserts list of rows."""

    try:
        cur = con.cursor()
        cur.executemany(sql, cards)
        con.commit()
    except Error as e:
        print(e)

def select_row(con, sql, val=()):
    """Method returns single result from selection query sql with parameters val."""

    try:
        cur = con.cursor()
        return cur.execute(sql, val).fetchone()
    except Error as e:
        print(e)

def select_rows(con, sql, val=()):
    """Same as select_row but instead returns all results."""

    try:
        cur = con.cursor()
        return cur.execute(sql, val).fetchall()
    except Error as e:
        print(e)

def table_initialization(con):
    """Method initializes tables by reading queries from file."""

    with open(path("initialize_database.sql"), 'r') as f:
        sql = f.read().split(';')
    if con is not None:
        for state in sql:
            create_table(con, state)