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

from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import oandapyV20.endpoints.accounts as accounts
import oandapyV20
import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.oanda_cred as oanda_cred
import q_tools.read_db as read_db
import q_tools.write_db as write_db

MASTER_LIST_FAILED_SYMBOLS = []

def load_data(symbol, symbol_id, conn, start_date,freq):
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
    client = oandapyV20.API(access_token=oanda_cred.token_practice)
    cur = conn.cursor()
    end_date = datetime.datetime.now()
    # if end_date.isoweekday() in set((6, 7)): # to take the nearest weekday
    #     end_date -= datetime.timedelta(days=end_date.isoweekday() % 5)

    print(start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),end_date.strftime("%Y-%m-%dT%H:%M:%SZ"))
    try:
        data = oanda_historical_data(granularity=freq.upper(),instrument=symbol,start_date=start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),end_date=end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),client=client)
    except:
        # sometimes the clocked is skewed and by few seconds off and the end date is in the future and that returns an error.
        if freq=='d':
            data = oanda_historical_data(granularity=freq.upper(),instrument=symbol,start_date=start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),end_date=(end_date-datetime.timedelta(seconds=60)).strftime("%Y-%m-%dT%H:%M:%SZ"),client=client)
        print("exception")
        MASTER_LIST_FAILED_SYMBOLS.append(symbol)
        raise Exception('Failed to load {}'.format(symbol))
    
    if data.empty:
        print(symbol," already updated")

    else:        
        # create new dataframe matching our table schema
        # and re-arrange our dataframe to match our database table
        columns_table_order = ['symbol_id', 'created_date', 
                               'last_updated_date', 'date_price', 'open_price',
                               'high_price', 'low_price', 'close_price', 'volume']
        newDF = pd.DataFrame()
        # For oanda each candle starts at UTC 22, so when the returned timestamp says 2020-01-09T22:00:00.000000000Z, it is actualy for 2020-01-10 
        # because the timestamp is the beginning of the candle (that is the open) and the close would be at 2020-01-10T22:00:00.000000000Z and therefore we need
        # to add a couple of hours so that it would be the next day and then we can extract the date to reflect the exact date.  This is not at all a neat way of 
        # doing it. Need to deal with timezone and should set timezone rules for consuming the data into the db.
        if freq=='d':
            newDF['date_price'] =  (data.index+pd.DateOffset(hours=3)).date
            date_diff = datetime.datetime.utcnow().date()-newDF['date_price'].max()
        else:
            newDF['date_price'] =  data.index
            date_diff = datetime.datetime.utcnow().date()-newDF['date_price'].max().date()

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

        # this is to avoid taking the data that's already in the DB.
        newDF.to_csv("before.csv")
        newDF=newDF[newDF['date_price']>pytz.utc.localize(start_date)] ## added 7/7/2020 10 PM #REF1
        newDF.to_csv("after.csv")
        # so that it leaves out the last incomplete candle 
        # the problem is that, this is an edge case. On Saturday or Sunday, this would only record till Thursday, so we are missing Friday. 
        # same situation for Weekly as well, that week wont be recorded till Monday till we have new incomplete data. Same goes for monthly as well. 
        # Right now I am checking if the last candle and the current time has a difference of more than 1 day. This will solve for the edge condition when we are running when the market closes on Friday but only if we are running the data load script on Saturday. 
        print("DATE_DIFF=",date_diff.days)
        if date_diff.days < 1:
            newDF=newDF[:-1]
        write_db.write_db_dataframe(df=newDF, conn=conn, table=(freq+'_data')) 
        print('{} complete!'.format(symbol))


def oanda_historical_data(instrument,start_date,end_date,granularity='D',client=None):
    params = {
    "from": start_date,
    "to": end_date,
    "granularity": granularity
    ,"count": 2500,
    }
    print(params)
    df_full=pd.DataFrame()
    for r in InstrumentsCandlesFactory(instrument=instrument,params=params):
        client.request(r)
        dat = []
        api_data=r.response.get('candles')
        if(api_data):
            for oo in r.response.get('candles'):
                dat.append([oo['time'], oo['volume'], oo['mid']['o'], oo['mid']['h'], oo['mid']['l'], oo['mid']['c']])
            df = pd.DataFrame(dat)
            df.columns = ['time', 'volume', 'open', 'high', 'low', 'close']
            df = df.set_index('time')
            if df_full.empty:
                df_full=df
            else:
                df_full=df_full.append(df)
    df_full.index=pd.to_datetime(df_full.index)    
    return df_full

def main(initial_start_date=datetime.datetime(2015,12,30),freq='d'):
    if type(initial_start_date)==str:
        datetime.datetime.strptime(initial_start_date, "%m-%d-%Y")   
    db_host=db_secmaster_cred.dbHost 
    db_user=db_secmaster_cred.dbUser
    db_password=db_secmaster_cred.dbPWD
    db_name=db_secmaster_cred.dbName

    # connect to our securities_master database
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)

    vendor = 'Oanda'
    sql="SELECT id FROM data_vendor WHERE name = '%s'" % (vendor)
    data_vendor_id=read_db.read_db_single(sql,conn) 

    s3 = boto3.client('s3',endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
    Bucket="airflow-files"
    Key="interested_tickers_oanda.xlsx"
    read_file = s3.get_object(Bucket=Bucket, Key=Key)
    df_tickers = pd.read_excel(io.BytesIO(read_file['Body'].read()),sep=',',sheet_name=freq)

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

        # Filling the empty dates returned from the DB with the initial start date
        df_ticker_last_day['last_date'].fillna(initial_start_date,inplace=True)

        # Adding 1 day, so that the data is appended starting next date # Commenting this because I believe the REF1 would solve this issue
        # if freq=='d':
        #     df_ticker_last_day['last_date']=df_ticker_last_day['last_date']+datetime.timedelta(days=1)
        # else:
        #     df_ticker_last_day['last_date']=df_ticker_last_day['last_date']+datetime.timedelta(minutes=1)

        # To see if the edge case of not recording the last hour of the weekend is solved
        # df_ticker_last_day['last_date']=df_ticker_last_day['last_date']-datetime.timedelta(minutes=1)

        startTime = datetime.datetime.now()

        print (datetime.datetime.now() - startTime)
        print(df_ticker_last_day)
        for i,stock in df_ticker_last_day.iterrows() :
            # download stock data and dump into daily_data table in our Postgres DB
            last_date = stock['last_date']
            symbol_id = stock['symbol_id']
            symbol = stock['ticker']
            try:
                print(symbol)
                load_data(symbol=symbol, symbol_id=symbol_id, conn=conn, start_date=last_date, freq=freq)
            except:
                print("exception")
                continue

        # lets write our failed stock list to text file for reference
        file_to_write = open('failed_symbols_oanda.txt', 'w')

        for symbol in MASTER_LIST_FAILED_SYMBOLS:
            file_to_write.write("%s\n" % symbol)

        print(datetime.datetime.now() - startTime)
if __name__ == "__main__":
    main()