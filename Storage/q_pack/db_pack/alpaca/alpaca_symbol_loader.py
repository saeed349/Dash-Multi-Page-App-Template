# -*- coding: utf-8 -*-
"""
@author: Saeed Rahman
"""
from __future__ import print_function

import datetime
import psycopg2
import os
import boto3
import io

import alpaca_trade_api as tradeapi
import configparser

import pandas as pd
import json

import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.alpaca_cred as alpaca_cred
import q_tools.read_db as read_db
import q_tools.write_db as write_db

def insert_symbols(conn,data_vendor_id):
    now = datetime.datetime.utcnow()
    api_key=alpaca_cred.api_key
    secret_key=alpaca_cred.secret_key
    api = tradeapi.REST(api_key, secret_key)
    active_assets = api.list_assets(status='active')
    symbols = []
    for symbol in active_assets:
        # if symbol.exchange=='NASDAQ':
        symbols.append({'ticker':symbol.symbol,'instrument':'Equity','name':symbol.name,'currency':'USD','shortable':symbol.shortable,'easy_to_borrow':symbol.easy_to_borrow,'marginable':symbol.marginable,'tradable':symbol.tradable,'status':symbol.status,'exchange':symbol.exchange,'data_vendor_id':data_vendor_id,'created_date':now,'last_updated_date':now})
            # symbols.append((symbol.symbol,'us_equity',symbol.name,'USD',symbol.shortable,symbol.easy_to_borrow,symbol.marginable,symbol.tradable,symbol.status,exchange_id,data_vendor_id,now,now))
    pd.DataFrame(symbols).to_csv('test.csv')
    write_db.write_db_dataframe(df=pd.DataFrame(symbols), conn=conn, table='symbol') 
    print("number of symbols loaded = ",len(symbols))

def main():
    db_host=db_secmaster_cred.dbHost 
    db_user=db_secmaster_cred.dbUser
    db_password=db_secmaster_cred.dbPWD
    db_name=db_secmaster_cred.dbName
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)    

    # exchange = 'NASDAQ'
    # exchange_id = []
    # sql="SELECT id FROM exchange WHERE abbrev = '%s'" % (exchange,)
    # exchange_id=read_db.read_db_single(sql,conn)
    # if exchange_id=='':
    #     exchange_abbrev = 'NASDAQ'
    #     exchange_name = 'National Association of Securities Dealers Automated Quotations'
    #     write_db.write_db_single(conn=conn, data_dict={'abbrev':exchange_abbrev,'name':exchange_name,'created_date':datetime.datetime.utcnow(),'last_updated_date':datetime.datetime.utcnow()}, table='exchange')
    #     print("Adding new Exchange ",exchange_name)
    #     sql="SELECT id FROM exchange WHERE abbrev = '%s'" % (exchange)
    #     exchange_id=read_db.read_db_single(sql,conn)

    vendor = 'Alpaca'
    data_vendor_id = []
    sql="SELECT id FROM data_vendor WHERE name = '%s'" % (vendor)
    data_vendor_id=read_db.read_db_single(sql,conn)
    if data_vendor_id=='':
        # insert_new_vendor(vendor, conn)
        write_db.write_db_single(conn=conn, data_dict={'name':vendor,'created_date':datetime.datetime.utcnow(),'last_updated_date':datetime.datetime.utcnow()}, table='data_vendor') 
        print("Adding new Vendor ",vendor)
        sql="SELECT id FROM data_vendor WHERE name = '%s'" % (vendor)
        data_vendor_id=read_db.read_db_single(sql,conn)

    insert_symbols(conn,data_vendor_id)    

if __name__ == "__main__":
    main()   