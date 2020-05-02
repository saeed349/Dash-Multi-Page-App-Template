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

# import q_credentials.db_secmaster_cloud_cred as db_secmaster_cred
import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.quandl_cred as quandl_cred
import q_tools.read_db as read_db
import q_tools.write_db as write_db

def insert_symbols(conn,exchange_id,data_vendor_id):
    now = datetime.datetime.utcnow()
    # ticker_info_file = "interested_tickers.xlsx"
    # cur_path = os.path.dirname(os.path.abspath(__file__))
    # f = os.path.join(cur_path,ticker_info_file)
    # df=pd.read_excel(f,sheet_name='Interested Symbols')
    s3 = boto3.client('s3',endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
    Bucket="airflow-files"
    Key="interested_tickers_quandl.xlsx"
    read_file = s3.get_object(Bucket=Bucket, Key=Key)
    df = pd.read_excel(io.BytesIO(read_file['Body'].read()),sep=',',sheet_name="Interested Symbols")
    df['instrument']='Equity'
    df['currency']='INR'
    df['exchange_id']=exchange_id
    df['data_vendor_id']=data_vendor_id
    df['created_date']=now
    df['last_updated_date']=now
    df=df.loc[:, df.columns != 'Quandl Code']
    write_db.write_db_dataframe(df=df, conn=conn, table='symbol') 
    print("Loaded Symbols=",len(df))


def main():
    db_host=db_secmaster_cred.dbHost 
    db_user=db_secmaster_cred.dbUser
    db_password=db_secmaster_cred.dbPWD
    db_name=db_secmaster_cred.dbName
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)    

    exchange = 'BSE'
    exchange_id = []
    sql="SELECT id FROM exchange WHERE abbrev = '%s'" % (exchange,)
    exchange_id=read_db.read_db_single(sql,conn)
    if exchange_id=='':
        exchange_abbrev = 'BSE'
        exchange_name = 'Bombay Stock Exchange'
        write_db.write_db_single(conn=conn, data_dict={'abbrev':exchange_abbrev,'name':exchange_name,'created_date':datetime.datetime.utcnow(),'last_updated_date':datetime.datetime.utcnow()}, table='exchange')
        print("Adding new Exchange ",exchange_name)
        sql="SELECT id FROM exchange WHERE abbrev = '%s'" % (exchange)
        exchange_id=read_db.read_db_single(sql,conn)

    vendor = 'Quandl'
    data_vendor_id = []
    sql="SELECT id FROM data_vendor WHERE name = '%s'" % (vendor)
    data_vendor_id=read_db.read_db_single(sql,conn)
    if data_vendor_id=='':
        # insert_new_vendor(vendor, conn)
        write_db.write_db_single(conn=conn, data_dict={'name':vendor,'created_date':datetime.datetime.utcnow(),'last_updated_date':datetime.datetime.utcnow()}, table='data_vendor') 
        print("Adding new Vendor ",vendor)
        sql="SELECT id FROM data_vendor WHERE name = '%s'" % (vendor)
        data_vendor_id=read_db.read_db_single(sql,conn)

    insert_symbols(conn,exchange_id,data_vendor_id)
    # print("%s symbols were successfully added." % len(symbols))  

    
if __name__ == "__main__":
    main()   