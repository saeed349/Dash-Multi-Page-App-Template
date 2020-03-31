# -*- coding: utf-8 -*-
"""
@author: Saeed Rahman
"""
from __future__ import print_function

import datetime
import psycopg2
import os

import alpaca_trade_api as tradeapi
import configparser

import pandas as pd
import json

import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.alpaca_cred as alpaca_cred

def get_symbols(conn,exchange_id,data_vendor_id):
    now = datetime.datetime.utcnow()
    api_key=alpaca_cred.api_key
    secret_key=alpaca_cred.secret_key
    api = tradeapi.REST(api_key, secret_key)
    active_assets = api.list_assets(status='active')

    symbols = []
    for symbol in active_assets:
        # if symbol.exchange=='NASDAQ':
        if True:
            symbols.append((symbol.symbol,'us_equity',symbol.name,'USD',symbol.shortable,symbol.easy_to_borrow,symbol.marginable,symbol.tradable,symbol.status,exchange_id,data_vendor_id,now,now))
    return symbols

def fetch_exchange_id(exchange, conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM exchange WHERE abbrev = %s", (exchange,))
    # will return a list of tuples
    exchange_id = cur.fetchall()
    # index to our first tuple and our first value
    exchange_id = exchange_id[0][0]
    return exchange_id   

def fetch_data_vendor_id(vendor, conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM data_vendor WHERE name = %s", (vendor,))
    # will return a list of tuples
    data_vendor_id = cur.fetchall()
    # index to our first tuple and our first value
    data_vendor_id = data_vendor_id[0][0]
    return data_vendor_id

def insert_exchange(abbrev, name, conn):
    todays_date = datetime.datetime.utcnow()
    cur = conn.cursor()
    cur.execute(
                "INSERT INTO exchange(abbrev, name, created_date, last_updated_date) VALUES (%s, %s, %s, %s)",
                (abbrev, name, todays_date, todays_date)
                )
    conn.commit()

def insert_new_vendor(vendor, conn):
    todays_date = datetime.datetime.utcnow()
    cur = conn.cursor()
    cur.execute(
                "INSERT INTO data_vendor(name, created_date, last_updated_date) VALUES (%s, %s, %s)",
                (vendor, todays_date, todays_date)
                )
    conn.commit()

def insert_symbols(symbols, conn):
    column_str = """
                 ticker,instrument,name,currency,shortable,easy_to_borrow,marginable,tradable,status,exchange_id,data_vendor_id,created_date, last_updated_date
                 """
    insert_str = ("%s, " * 13)[:-2]
    final_str = "INSERT INTO symbol (%s) VALUES (%s)" % (column_str, insert_str)
    with conn:
        cur = conn.cursor()
        cur.executemany(final_str, symbols)

def main():
    db_host=db_secmaster_cred.dbHost 
    db_user=db_secmaster_cred.dbUser
    db_password=db_secmaster_cred.dbPWD
    db_name=db_secmaster_cred.dbName
    # Connect to our PostgreSQL database
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)    

    exchange = 'NASDAQ'
    exchange_id = []
    try:
        exchange_id = fetch_exchange_id(exchange, conn)
    except:
        exchange_abbrev = 'NASDAQ'
        exchange_name = 'National Association of Securities Dealers Automated Quotations'
        insert_exchange(exchange_abbrev, exchange_name, conn) 
        print("Adding new Exchange ",exchange_name)
        exchange_id = fetch_exchange_id(exchange, conn)

    vendor = 'Alpaca-IEX'
    data_vendor_id = []
    try:
        data_vendor_id = fetch_data_vendor_id(vendor, conn)
    except:
        insert_new_vendor(vendor, conn) 
        print("Adding new Vendor ",vendor)
        data_vendor_id = fetch_data_vendor_id(vendor, conn)

    symbols = get_symbols(conn,exchange_id,data_vendor_id)
    insert_symbols(symbols, conn) #pd.DataFrame(symbols).to_csv("alpaca_symbols2.csv")
    print("%s symbols were successfully added." % len(symbols))  

    
    
if __name__ == "__main__":
    main()   