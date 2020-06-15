# -*- coding: utf-8 -*-
"""
Created on 8/31/2019

@author: Saeed Rahman
"""
from __future__ import print_function

import datetime
import psycopg2
import os


import oandapyV20
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.instruments as instruments
import configparser

import pandas as pd
import json

import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.oanda_cred as oanda_cred
import q_tools.read_db as read_db
import q_tools.write_db as write_db

def insert_symbols(conn,data_vendor_id):
    now = datetime.datetime.utcnow()
    accountID=oanda_cred.acc_id_practice
    token=oanda_cred.token_practice
    client = oandapyV20.API(access_token=token)
    r = accounts.AccountInstruments(accountID=accountID)
    rv = client.request(r)

    df=pd.read_json(json.dumps(rv, indent=2))
    df=pd.io.json.json_normalize(data=df['instruments'])

    symbols = []
    for i,symbol in df.iterrows():
        symbols.append({'ticker':symbol['name'],'instrument':'Forex','name':symbol['displayName'],'data_vendor_id':data_vendor_id,'created_date':now,'last_updated_date':now})
    write_db.write_db_dataframe(df=pd.DataFrame(symbols), conn=conn, table='symbol') 
    print("number of symbols loaded = ",len(symbols))  

def main():
    db_host=db_secmaster_cred.dbHost 
    db_user=db_secmaster_cred.dbUser
    db_password=db_secmaster_cred.dbPWD
    db_name=db_secmaster_cred.dbName
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
    
    vendor = 'Oanda'
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