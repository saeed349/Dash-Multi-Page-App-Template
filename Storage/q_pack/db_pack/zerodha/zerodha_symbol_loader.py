# -*- coding: utf-8 -*-
"""
Created on 8/31/2019

@author: Saeed Rahman
"""
from __future__ import print_function

import datetime
import psycopg2
import os
import requests
import configparser
import pandas as pd
import json
import boto3
import io

import q_credentials.zerodha_cred as zerodha_cred
import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.zerodha_cred as zerodha_cred
import q_tools.read_db as read_db
import q_tools.write_db as write_db
import q_tools.zerodha_authentication as zerodha_authentication

def insert_symbols(conn,data_vendor_id):
    now = datetime.datetime.utcnow()
    kite = zerodha_authentication.zerodha_authentication(
        api_key=zerodha_cred.api_key,
        api_secret=zerodha_cred.api_secret,
        userid=zerodha_cred.userid,
        password=zerodha_cred.password,
        pin=zerodha_cred.pin
        )
    
    df_instruments=pd.DataFrame(kite.instruments())

    # getting the top 1000 market cap equity symbols
    s3 = boto3.client('s3',endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
    Bucket="airflow-files"
    Key="interested_tickers_india.xlsx"
    read_file = s3.get_object(Bucket=Bucket, Key=Key)
    df_tickers = pd.read_excel(io.BytesIO(read_file['Body'].read()),sheet_name='nse_top_1000')
    # merging the top1000 with the data from zerodha
    df_symbols=pd.merge(df_instruments,df_tickers,left_on='tradingsymbol',right_on='Symbol',how='inner')
    df_symbols=df_symbols.sort_values(by=['tradingsymbol','exchange']).drop_duplicates(subset=['tradingsymbol'],keep='last') # just to keep nse (last when sorted)
    columns_dict={'instrument_token':'identifier','tradingsymbol':'ticker'}
    df_symbols=df_symbols[['instrument_token','tradingsymbol','name','exchange']].rename(columns=columns_dict)
    df_symbols['instrument']='Equity'
    df_symbols['data_vendor_id']=data_vendor_id
    df_symbols['created_date']=now
    df_symbols['last_updated_date']=now

    write_db.write_db_dataframe(df=df_symbols, conn=conn, table='symbol') 
    print("number of symbols loaded = ",len(df_symbols))  

def main():
    db_host=db_secmaster_cred.dbHost 
    db_user=db_secmaster_cred.dbUser
    db_password=db_secmaster_cred.dbPWD
    db_name=db_secmaster_cred.dbName
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
    
    vendor = 'Zerodha'
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