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
           "delete from tri;")
    cur = con.cursor()
    for state in sql:
        cur.execute(state)
    con.commit()

def get_set(text):
    """Method takes as input a text string of the form: set_code - set_name (release_date) [# of cards in set]
    API is queried with given set information
    """
    pack_code, pack = text.split(' - ')[0:2]
    release = [int(date) for date in text.split(' - ')[2].split()[0][1:-1].split('-')]
    pack_date = datetime.date(release[0], release[1], release[2])
    pack_size = text.split(' - ')[2].split()[1][1:-1]

    URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php?cardset=" + pack.replace(" ", "%20")
    r = requests.get(URL)
    df = pd.DataFrame(r.json()["data"])
    
    codes = []
    rarity = []
    for card in df['card_sets']:
        try:
            # codes.append(next((item['set_code'] for item in card if item["set_name"].endswith(pack)), "Err"))
            codes.append([item['set_code'] for item in card if item['set_name'].endswith(pack)])
        except TypeError:
            codes.append("Err")
        try:
            # rarity.append(next((item['set_rarity_code'] for item in card if item["set_name"].endswith(pack)), "Err"))
            rarity.append([item['set_rarity_code'] for item in card if item['set_name'].endswith(pack)])
        except TypeError:
            rarity.append("Err")

    setCodes = pd.Series(codes, name='set_code')
    setRarity = pd.Series(rarity, name='rarity')
    ind, cols = pd.factorize(df['id'])
    for card in df['id']:
        col = cols.get_loc(card)
        df.at[col, 'id'] = str(card).zfill(8)

    df = pd.concat([df, setCodes, setRarity], axis=1)
    df = df[["id", "name", "set_code", "rarity"]]
    df = df.explode(['set_code', 'rarity'])
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
        id = elem[0]
        set_code = elem[1]
        name = elem[2]
        rarity = elem[3]
        cards.append((id, name, pack_code, set_code, rarity, 0))

    return [(pack_code, pack, pack_size, pack_date, None), cards]

def set_info(sets):
    try:
        c = Counter([d['set_code'].split('-')[0] for d in sets])
        items, codes = [], []
        for dicts in sets:
            set_code = dicts['set_code'].split('-')
            rarity = dicts['set_rarity_code']
            if (c[set_code[0]] == 1 or 'EN' in set_code[1] or len(set_code[1]) == 3) & (set_code[0] not in codes or ):
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
            card_formats.append((card['id'], card['name'], elem))

    return all_cards, card_sets, banlist, card_formats

def get_info_2(df):
    df = df.convert_dtypes(convert_integer=True) # Convert columns with numeric data to integers
    dates = pd.json_normalize(df['misc_info'].apply(lambda x: x[0])) # Extract dates
    df = pd.concat([df, dates.drop(list(set(dates.columns)-{'formats', 'tcg_date', 'ocg_date'}), axis=1)], axis=1) # Add dates and format to dataframe
    df = df.reindex(columns=['id', 'name', 'type', 'desc', 'race', 'archetype', 'atk', 'def', 'level', 'attribute', 'scale', 'linkval',
                             'tcg_date', 'ocg_date', 'formats', 'banlist_info', 'card_sets']) # Re-index dataframe
    cards = df.replace({pd.NA: None}).to_numpy() # Replaces NaN with None type for SQLite and convert dataframe to numpy array
    cols = list(df.columns)

    meta = {'all_cards': [], 'card_sets': [], 'card_formats': [], 'banlist': []} # Dictionary to contain card metadata

    for i in range(df.shape[0]):
        ban = {'ban_tcg': None, 'ban_ocg': None, 'ban_goat': None}
        card = {key: val for key, val in zip(cols, cards[i])}  # Initialize dictionary with data for single card
        sets = card['card_sets']
        formats = card['formats']
        card['id'] = str(card['id']).zfill(8)  # Ensure the card password is 8 characters long by front filling with 0's

        if card['banlist_info'] is not None:  # Check if card is on any banlists
            ban.update(card['banlist_info'])

        meta['all_cards'].append(tuple(card.values())[:-3])  # Add card data to list of all cards, removing formats, banlist, and card_sets columns
        meta['banlist'].append((card['id'], card['name']) + tuple(ban.values()))

        if sets is not None:
            items = set_info(sets)
            vals = [(elem['set_code'].split('-')[0], elem['set_code'], elem['set_rarity'], elem['set_rarity_code']) for elem in items]  # Proper formatting for set info
            for row in vals:
                meta['card_sets'].append((card['id'], card['name']) + row)
        
        for elem in formats:
            meta['card_formats'].append((card['id'], card['name'], elem))

    return meta


def insert_info(con, df):
    """Method re-populates card database. Must first format data to consistent form."""
    all_cards, card_sets, card_formats, banlist = get_info(df).values()
    # Insert data into database
    insert_rows(con, 'insert into all_cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', all_cards)
    insert_rows(con, 'insert into sets values (?,?,?,?,?,?)', card_sets)
    insert_rows(con, 'insert into formats values (?,?,?)', card_formats)
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
    with open(asset_path('set_list.json'), 'w') as f:
        f.write(json.dumps(all_sets, indent=4)) # Update set list JSON file
    r = requests.get("https://db.ygoprodeck.com/api/v7/checkDBVer.php")
    vals = (r.json()[0]['database_version'], r.json()[0]['last_update'].split()[0])
    insert_row(con, "update db_version set version=?, date=?", vals)
    toc = time.perf_counter()
    print(f'Done! It took {toc-tic:.4f} seconds.')