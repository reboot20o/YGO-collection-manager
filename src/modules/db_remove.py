from modules.create_db import insert_row, select_rows, insert_rows
from modules.location_designation import asset_path
import requests
import pandas as pd
import numpy as np
from collections import Counter
import json
import datetime
import time

def clear_tables(con):
    """Method clears contents from tables"""

    sql = ("delete from all_cards;", "delete from sets;", "delete from banlist;", "delete from formats;",
           "delete from tri;", "delete from all_sets;", "delete from sets_tri;")
    cur = con.cursor()
    for state in sql:
        cur.execute(state)
    con.commit()

def get_set(text):
    """Method takes as input a text string of the form: set_code - set_name - (release_date) - [# of cards in set]
    API is queried with given set information
    """
    data = text.split(' - ')
    if len(data) > 4:
        data[1] = '-'.join(data[1:-2])
        del data[2:-2]
    pack_code, pack, release_date, size = data
    release = [int(date) for date in release_date[1:-1].split('-')]
    pack_date = datetime.date(release[0], release[1], release[2])
    pack_size = size[1:-1]

    URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php?cardset=" + pack.replace(" ", "%20")
    r = requests.get(URL)
    df = pd.DataFrame(r.json()["data"])
    
    codes = []
    rarity = []
    for card in df['card_sets']:
        try:
            # codes.append(next((item['set_code'] for item in card if item["set_name"].endswith(pack)), "Err"))
            codes.extend((item['set_code'] for item in card if item['set_name'].endswith(pack)))
        except TypeError:
            codes.append("Err")
        try:
            # rarity.append(next((item['set_rarity_code'] for item in card if item["set_name"].endswith(pack)), "Err"))
            rarity.extend((item['set_rarity_code'] for item in card if item['set_name'].endswith(pack)))
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
            try:
                df.loc[i, 'set_code'] = temp[:-3] + str(int(temp[-3:])+1).zfill(3)
            except ValueError:
                df.loc[i, 'set_code'] = temp[:-2] + str(int(temp[-2:])+1).zfill(2)

    set_list = df.to_numpy()
    cards = []
    for elem in set_list:
        id, set_code, name, rarity = elem
        cards.append((id, name, pack_code, set_code, rarity, 0))

    return [(pack_code, pack, pack_size, pack_date, None), cards]

def set_info(sets):
    try:
        c = Counter([d['set_code'].split('-')[0] for d in sets])
        items, codes = [], []
        for dicts in sets:
            set_code = dicts['set_code'].split('-')
            if c[set_code[0]] == 1 or 'EN' in set_code[1] or len(set_code[1]) == 3:
                items.append(dicts)
                codes.append(set_code[0])
        return items
    except IndexError:
        pass

def get_info(df):
    df = df.replace({np.nan: None})  # Replaces NaN with None type so SQLite thinks it's Null
    cards = df.to_numpy()
    ints = ['atk', 'def', 'level', 'scale', 'linkval']  # Columns with numeric data
    cols = list(df.columns)
    remove = ['card_sets', 'card_images', 'card_prices', 'misc_info', 'banlist_info', 'linkmarkers',
              'frameType', 'pend_desc', 'monster_desc']  # Columns to remove
    all_cards = []  # List of all cards represented as tuples
    card_sets = []  # Set metadata
    card_formats = []
    banlist = []
    for i in range(df.shape[0]):
        ban = {'ban_tcg': None, 'ban_ocg': None, 'ban_goat': None}
        card = {key: val for key, val in zip(cols, cards[i])}  # Initialize dictionary with data for single card
        card['tcg'], card['ocg'] = None, None
        for j in ints:
            if card[j] is not None:
                card[j] = int(card[j])  # Change numeric data from String to Int
        card['id'] = str(card['id']).zfill(8)  # Ensure the card password is 8 characters long by front filling with 0's
        sets = card['card_sets']
        formats = card['misc_info'][0]['formats']
        if 'tcg_date' in card['misc_info'][0].keys():  # Check if card was released in the TCG or OCG
            card['tcg'] = card['misc_info'][0]['tcg_date']
        if 'ocg_date' in card['misc_info'][0].keys():
            card['ocg'] = card['misc_info'][0]['ocg_date']
        if card['banlist_info'] is not None:  # Check if card is on any banlists
            ban.update(card['banlist_info'])
        for x in remove:  # Remove irrelevant columns
            card.pop(x)

        all_cards.append(tuple(card.values()))  # Add card data to list of all cards
        banlist.append((card['id'], card['name']) + tuple(ban.values()))
        if sets is not None:
            items = set_info(sets)
            vals = [(elem['set_code'].split('-')[0], elem['set_code'], elem['set_rarity'], elem['set_rarity_code']) for
                    elem in items]  # Proper formatting for set info
            for row in vals:
                card_sets.append((card['id'], card['name']) + row)
        for elem in formats:
            card_formats.append((card['name'], elem))

    return all_cards, card_sets, banlist, card_formats

def get_info_2(df):
    df = df.replace({np.nan: None})  # Replaces NaN with None type so SQLite thinks it's Null
    cards = df.to_numpy()
    ints = ['atk', 'def', 'level', 'scale', 'linkval']  # Columns with numeric data
    cols = list(df.columns)
    remove = ['card_sets', 'card_images', 'card_prices', 'misc_info', 'banlist_info', 'linkmarkers',
              'frameType']  # Columns to remove
    all_cards = []  # List of all cards represented as tuples
    card_sets = []  # Set metadata
    card_formats = []
    banlist = []

    for i in range(df.shape[0]):
        ban = {'ban_tcg': None, 'ban_ocg': None, 'ban_goat': None}
        card = {key: val for key, val in zip(cols, cards[i])}  # Initialize dictionary with data for single card
        card['tcg'], card['ocg'] = None, None

        for j in ints:
            try:
                if card[j] is not None:
                    card[j] = int(card[j])  # Change numeric data from String to Int
            except KeyError:
                card[j] = None
        
        card['id'] = str(card['id']).zfill(8)  # Ensure the card password is 8 characters long by front filling with 0's
        sets = card['card_sets']
        formats = card['misc_info'][0]['formats']

        if 'tcg_date' in card['misc_info'][0].keys():  # Check if card was released in the TCG or OCG
            card['tcg'] = card['misc_info'][0]['tcg_date']
        if 'ocg_date' in card['misc_info'][0].keys():
            card['ocg'] = card['misc_info'][0]['ocg_date']
        try:
            if card['banlist_info'] is not None:  # Check if card is on any banlists
                ban.update(card['banlist_info'])
        except:
            pass
        
        try:
            for x in remove:  # Remove irrelevant columns
                card.pop(x)
        except:
            pass

        all_cards.append(tuple(card.values()))  # Add card data to list of all cards
        banlist.append((card['id'], card['name']) + tuple(ban.values()))

        if sets is not None:
            items = set_info(sets)
            vals = [(elem['set_code'].split('-')[0], elem['set_code'], elem['set_rarity'], elem['set_rarity_code']) for
                    elem in items]  # Proper formatting for set info
            for row in vals:
                card_sets.append((card['id'], card['name']) + row)
        
        for elem in formats:
            card_formats.append((card['id'], card['name'], elem))

    return all_cards, card_sets, banlist, card_formats


def insert_info(con, df):
    """Method re-populates card database. Must first format data to consistent form."""
    all_cards, card_sets, banlist, card_formats = get_info(df)
    # Insert data into database
    insert_rows(con, 'insert into all_cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', all_cards)
    insert_rows(con, 'insert into sets values (?,?,?,?,?,?)', card_sets)
    insert_rows(con, 'insert into formats values (?,?)', card_formats)
    insert_rows(con, 'insert into banlist values (?,?,?,?,?)', banlist)
    tri = select_rows(con, "select name, archetype from all_cards;")
    insert_rows(con, "insert into tri values (?,?);", tri)


def update_tables(con):
    """Method updates the tables. Starts by clearing original contents, then re-populating. Fine for now since tables
    only have ~12,000 rows, but probably bad practice. Should switch to update entries with changes, but limited by
    info provided by api."""
    print('Now populating tables...')
    tic = time.perf_counter()
    clear_tables(con)
    r = requests.get("https://db.ygoprodeck.com/api/v7/cardinfo.php?misc=yes")
    df = pd.DataFrame(r.json()['data'])
    insert_info(con, df) # Calls method to insert request data into database
    all_sets = requests.get("https://db.ygoprodeck.com/api/v7/cardsets.php").json()
    rows = []
    for row in all_sets:
        if 'tcg_date' not in row.keys():
            row['tcg_date'] = None
        if row['set_name'] == 'Dark Beginning 1':
            row['set_code'] = 'DB1'
        rows.append((row['set_name'], row['set_code'], row['num_of_cards'], row['tcg_date']))
    insert_rows(con, "insert into all_sets values (?,?,?,?);", rows)
    tri = select_rows(con, "select name, code from all_sets;")
    insert_rows(con, "insert into sets_tri values (?,?)", tri)
    with open(asset_path('set_list.json'), 'w') as f:
        f.write(json.dumps(all_sets, indent=4)) # Update set list JSON file
    r = requests.get("https://db.ygoprodeck.com/api/v7/checkDBVer.php")
    vals = (r.json()[0]['database_version'], r.json()[0]['last_update'].split()[0])
    insert_row(con, "update db_version set version=?, date=?", vals)
    toc = time.perf_counter()
    print(f'Done! It took {toc-tic:.4f} seconds.')