"""
Created: October 06 2019 2018

Aauthor: Saeed Rahman

Use Case: Download Historical Data for Forex Majors and update the DB based on the interested_tickers.csv

Successful Test Cases: 
 - daily_data table is empty
 - only 1 ticker in the interested_tickers.csv (comma appended at the end of tuple)
 - No items in interested_tickers.csv
 - There are missing as well new (new to daily_data) items in the interested_ticker.csv

Future work:
 - File Paths dynamic
 - Parameterize
    * Filelocation 
    * DB Details and Credential
    * DB Table
 - Add Date Range in interested_tickers.csv
"""

import datetime
import psycopg2
import pandas as pd
import os
import io
import boto3
import pytz


import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.oanda_cred as oanda_cred
import q_tools.read_db as read_db
import q_tools.write_db as write_db
import q_tools.zerodha_authentication as zerodha_authentication
import q_credentials.zerodha_cred as zerodha_cred

MASTER_LIST_FAILED_SYMBOLS = []

def load_data(symbol, symbol_id, conn, start_date,freq,kite):
    """
    This will load stock data (date+OHLCV) and additional info to our daily_data table.
    args:
        symbol: stock ticker, type string.
        symbol_id: stock id referenced in symbol(id) column, type integer.
        vendor_id: data vendor id referenced in data_vendor(id) column, type integer.
        conn: a Postgres DB connection object
    return:
        None
    """
    cur = conn.cursor()
    end_date = datetime.datetime.now()
    # if end_date.isoweekday() in set((6, 7)): # to take the nearest weekday
    #     end_date -= datetime.timedelta(days=end_date.isoweekday() % 5)
    # end_date -= datetime.timedelta(days=1) # temporary

    print(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
    # try:
    data = pd.DataFrame(kite.historical_data(instrument_token=str(symbol),from_date=start_date.strftime("%Y-%m-%d"),to_date=end_date.strftime("%Y-%m-%d"),interval='day'))
    # data = pd.DataFrame(kite.historical_data(instrument_token=symbol,from_date=start_date.strftime("%Y-%m-%d"),interval='day'))
    data=data.set_index(pd.to_datetime(data['date']))
    if data.empty:
        print(symbol," already updated")

    else:        
        columns_table_order = ['symbol_id', 'created_date', 
                               'last_updated_date', 'date_price', 'open_price',
                               'high_price', 'low_price', 'close_price', 'volume']
        newDF = pd.DataFrame()
        newDF['date_price'] =  (data.index).date
        date_diff = datetime.datetime.utcnow().date()-newDF['date_price'].max()
        data.reset_index(drop=True,inplace=True)
        newDF['open_price'] = data['open']
        newDF['high_price'] = data['high']
        newDF['low_price'] = data['low']
        newDF['close_price'] = data['close']
        newDF['volume'] = data['volume']
        newDF['symbol_id'] = symbol_id
        newDF['created_date'] = datetime.datetime.utcnow()
        newDF['last_updated_date'] = datetime.datetime.utcnow()
        newDF = newDF[columns_table_order]
        # ensure our data is sorted by date
        newDF = newDF.sort_values(by=['date_price'], ascending = True)
        newDF=newDF[newDF['date_price']>pytz.utc.localize(start_date)]
        print("DATE_DIFF=",date_diff.days)
        if date_diff.days < 1:
            newDF=newDF[:-1]
        write_db.write_db_dataframe(df=newDF, conn=conn, table=(freq+'_data')) 
        print('{} complete!'.format(symbol))

def main(initial_start_date=datetime.datetime(2015,12,30),freq='d'):
    if type(initial_start_date)==str:
        datetime.datetime.strptime(initial_start_date, "%m-%d-%Y")   
    db_host=db_secmaster_cred.dbHost 
    db_user=db_secmaster_cred.dbUser
    db_password=db_secmaster_cred.dbPWD
    db_name=db_secmaster_cred.dbName

    # connect to our securities_master database
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)

    vendor = 'Zerodha'
    sql="SELECT id FROM data_vendor WHERE name = '%s'" % (vendor)
    data_vendor_id=read_db.read_db_single(sql,conn) 

    s3 = boto3.client('s3',endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
    Bucket="airflow-files"
    Key="interested_tickers_india.xlsx"
    read_file = s3.get_object(Bucket=Bucket, Key=Key)
    df_tickers = pd.read_excel(io.BytesIO(read_file['Body'].read()),sheet_name=freq)

    if df_tickers.empty:
        print("Empty Ticker List")
    else:
        # Getting the last date for each interested tickers
        sql="""select a.last_date, b.id as symbol_id, b.ticker from
            (select max(date_price) as last_date, symbol_id
            from {}_data 
            group by symbol_id) a right join symbol b on a.symbol_id = b.id 
            where b.ticker in {} and b.data_vendor_id={}""".format(freq,str(tuple(df_tickers['Tickers'])).replace(",)", ")"),data_vendor_id)
        df_ticker_last_day=pd.read_sql(sql,con=conn)

        kite = zerodha_authentication.zerodha_authentication(
        api_key=zerodha_cred.api_key,
        api_secret=zerodha_cred.api_secret,
        userid=zerodha_cred.userid,
        password=zerodha_cred.password,
        pin=zerodha_cred.pin
        )
        df_instruments=pd.DataFrame(kite.instruments())
        df_ticker_last_day=pd.merge(df_instruments,df_ticker_last_day,left_on='tradingsymbol',right_on='ticker',how='right')
        df_ticker_last_day=df_ticker_last_day.sort_values(by=['tradingsymbol','exchange']).drop_duplicates(subset=['tradingsymbol'],keep='last')
        # df_ticker_last_day.to_csv('zerodha_ticker.csv')
        # Filling the empty dates returned from the DB with the initial start date
        df_ticker_last_day['last_date'].fillna(initial_start_date,inplace=True)

        startTime = datetime.datetime.now()

        print (datetime.datetime.now() - startTime)
        # print(df_ticker_last_day)
        for i,stock in df_ticker_last_day.iterrows() :
            # download stock data and dump into daily_data table in our Postgres DB
            last_date = stock['last_date']
            symbol_id = stock['symbol_id']
            symbol = stock['instrument_token']
            # try:
            print(symbol)
            load_data(symbol=symbol, symbol_id=symbol_id, conn=conn, start_date=last_date, freq=freq,kite=kite)
            # except:
            #     print("exception")
            #     continue

        # lets write our failed stock list to text file for reference
        file_to_write = open('failed_symbols_oanda.txt', 'w')

        for symbol in MASTER_LIST_FAILED_SYMBOLS:
            file_to_write.write("%s\n" % symbol)

        print(datetime.datetime.now() - startTime)
if __name__ == "__main__":
    main()