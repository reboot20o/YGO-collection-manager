from modules.create_db import insert_row, select_rows, insert_rows
from modules.location_designation import path
import requests
import pandas as pd
import numpy as np
from collections import Counter
import json

def clear_tables(con):
    """Method clears contents from tables"""

    sql = ("delete from all_cards;", "delete from sets;", "delete from banlist;", "delete from formats;",
           "delete from tri;")
    cur = con.cursor()
    for state in sql:
        cur.execute(state)
    con.commit()

def insert_info(con, df):
    """Method re-populates card database. Must first format data to consistent form."""

    df = df.replace({np.nan: None}) # Replaces NaN with None type so SQLite thinks it's Null
    cards = df.to_numpy()
    ints = ['atk', 'def', 'level', 'scale', 'linkval'] # Columns with numeric data
    cols = list(df.columns)
    remove = ['card_sets', 'card_images', 'card_prices', 'misc_info', 'banlist_info', 'linkmarkers'] # Columns to remove
    all_cards = [] # List of all cards represented as tuples
    card_sets = [] # Set metadata
    card_formats = []
    banlist = []
    for i in range(df.shape[0]):
        ban = {'ban_tcg': None, 'ban_ocg': None, 'ban_goat': None}
        card = {key: val for key, val in zip(cols, cards[i])} # Initialize dictionary with data for single card
        card['tcg'], card['ocg'] = None, None
        for j in ints:
            if card[j] is not None:
                card[j] = int(card[j]) # Change numeric data from String to Int
        card['id'] = str(card['id']).zfill(8) # Ensure the card password is 8 characters long by front filling with 0's
        sets = card['card_sets']
        formats = card['misc_info'][0]['formats']
        if 'tcg_date' in card['misc_info'][0].keys(): # Check if card was released in the TCG or OCG
            card['tcg'] = card['misc_info'][0]['tcg_date']
        if 'ocg_date' in card['misc_info'][0].keys():
            card['ocg'] = card['misc_info'][0]['ocg_date']
        if card['banlist_info'] is not None: # Check if card is on any banlists
            ban.update(card['banlist_info'])
        for x in remove: # Remove irrelevant columns
            card.pop(x)

        all_cards.append(tuple(card.values())) # Add card data to list of all cards
        banlist.append((card['id'], card['name'])+tuple(ban.values()))
        if sets is not None:
            c = Counter([d['set_name'] for d in sets])
            items = [d for d in sets if c[d['set_name']] == 1 or 'EN' in d['set_code']] # Only take English sets if there's an option
            vals = [(elem['set_code'].split('-')[0], elem['set_code'], elem['set_rarity'], elem['set_rarity_code']) for
                    elem in items] # Proper formatting for set info
            for row in vals:
                card_sets.append((card['id'], card['name'])+row)
        for elem in formats:
            card_formats.append((card['name'], elem))

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

    clear_tables(con)
    r = requests.get("https://db.ygoprodeck.com/api/v7/cardinfo.php?misc=yes")
    df = pd.DataFrame(r.json()['data'])
    insert_info(con, df) # Calls method to insert request data into database
    all_sets = requests.get("https://db.ygoprodeck.com/api/v7/cardsets.php").json()
    with open(path('set_list.json'), 'w') as f:
        f.write(json.dumps(all_sets, indent=4)) # Update set list JSON file
    r = requests.get("https://db.ygoprodeck.com/api/v7/checkDBVer.php")
    vals = (r.json()[0]['database_version'], r.json()[0]['last_update'].split()[0])
    insert_row(con, "update db_version set version=?, date=?", vals)