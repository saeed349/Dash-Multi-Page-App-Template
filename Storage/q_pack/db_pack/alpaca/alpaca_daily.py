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

import alpaca_trade_api as tradeapi
import q_credentials.alpaca_cred as alpaca_cred
import q_credentials.db_secmaster_cred as db_secmaster_cred
MASTER_LIST_FAILED_SYMBOLS = []



def obtain_list_db_tickers(conn, vendor_name):
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT s.id, s.ticker FROM symbol s INNER JOIN data_vendor v ON (s.data_vendor_id = v.id) where v.name = %s", (vendor_name,)) 
        data = cur.fetchall()
        return [(d[0], d[1]) for d in data]

def fetch_data_vendor_id(vendor, conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM data_vendor WHERE name = %s", (vendor,))
    data_vendor_id = cur.fetchall()
    data_vendor_id = data_vendor_id[0][0]
    return data_vendor_id

def load_data(symbol, symbol_id, conn, start_date):
    api_key=alpaca_cred.api_key
    secret_key=alpaca_cred.secret_key
    api = tradeapi.REST(api_key, secret_key)

    cur = conn.cursor()
    end_dt = datetime.datetime.now()
    if end_dt.isoweekday() in set((6, 7)): # to take the nearest weekday
        end_dt -= datetime.timedelta(days=end_dt.isoweekday() % 5)
    
    try:
        data = api.get_barset([symbol], 'day', start=start_date).df[symbol] # the start_date functionality is not working with Alpaca
        # data = yf.download(symbol, start=start_dt, end=end_dt)
    except:
        MASTER_LIST_FAILED_SYMBOLS.append(symbol)
        raise Exception('Failed to load {}'.format(symbol))

    if data.empty:
        print(symbol," already updated")

    else:        
        # create new dataframe matching our table schema
        # and re-arrange our dataframe to match our database table
        columns_table_order = ['stock_id', 'created_date', 
                               'last_updated_date', 'date_price', 'open_price',
                               'high_price', 'low_price', 'close_price', 'volume']
        newDF = pd.DataFrame()
        newDF['date_price'] =  (data.index).date
        data.reset_index(drop=True,inplace=True)
        newDF['open_price'] = data['open']
        newDF['high_price'] = data['high']
        newDF['low_price'] = data['low']
        newDF['close_price'] = data['close']
        newDF['volume'] = data['volume']
        newDF['stock_id'] = symbol_id
        newDF['created_date'] = datetime.datetime.utcnow()
        newDF['last_updated_date'] = datetime.datetime.utcnow()
        newDF = newDF[columns_table_order]


        # ensure our data is sorted by date
        newDF = newDF.sort_values(by=['date_price'], ascending = True)

        print(newDF['stock_id'].unique())
        print(newDF['date_price'].min())
        print(newDF['date_price'].max())
        print("")

        # convert our dataframe to a list
        list_of_lists = newDF.values.tolist()
        # convert our list to a list of tuples       
        tuples_mkt_data = [tuple(x) for x in list_of_lists]

        # WRITE DATA TO DB
        insert_query =  """
                        INSERT INTO daily_data (stock_id, created_date,
                        last_updated_date, date_price, open_price, high_price, low_price, close_price, volume) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
        cur.executemany(insert_query, tuples_mkt_data)
        conn.commit()    
        print('{} complete!'.format(symbol))


def main():

    initial_start_date = datetime.datetime(2010,12,30)
    
    db_host=db_secmaster_cred.dbHost 
    db_user=db_secmaster_cred.dbUser
    db_password=db_secmaster_cred.dbPWD
    db_name=db_secmaster_cred.dbName

    # connect to our securities_master database
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)

    vendor = 'Alpaca-IEX'
    data_vendor_id = fetch_data_vendor_id(vendor, conn)

    # s3 = boto3.client('s3',endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
    # Bucket="airflow-files"
    # Key="interested_tickers.xlsx"
    # read_file = s3.get_object(Bucket=Bucket, Key=Key)
    # df_tickers = pd.read_excel(io.BytesIO(read_file['Body'].read()),sep=',',sheet_name="daily")


    ticker_info_file = "interested_tickers_equity.xlsx"
    cur_path = os.path.dirname(os.path.abspath(__file__))
    f = os.path.join(cur_path,ticker_info_file)
    df_tickers=pd.read_excel(f,sheet_name='daily')

    if df_tickers.empty:
        print("Empty Ticker List")
    else:
        # Getting the last date for each interested tickers
        sql="""select a.last_date, b.id as stock_id, b.ticker from
            (select max(date_price) as last_date, stock_id
            from daily_data 
            group by stock_id) a right join symbol b on a.stock_id = b.id 
            where b.ticker in {} and b.data_vendor_id={}""".format(str(tuple(df_tickers['Tickers'])).replace(",)", ")"),data_vendor_id)
        df_ticker_last_day=pd.read_sql(sql,con=conn)

        # Filling the empty dates returned from the DB with the initial start date
        df_ticker_last_day['last_date'].fillna(initial_start_date,inplace=True)

        # Adding 1 day, so that the data is appended starting next date
        df_ticker_last_day['last_date']=df_ticker_last_day['last_date']+datetime.timedelta(days=1)
        
        startTime = datetime.datetime.now()

        print (datetime.datetime.now() - startTime)

        for i,stock in df_ticker_last_day.iterrows() :
            # download stock data and dump into daily_data table in our Postgres DB
            last_date = stock['last_date']
            symbol_id = stock['stock_id']
            symbol = stock['ticker']
            try:
                load_data(symbol=symbol, symbol_id=symbol_id, conn=conn, start_date=last_date)
            except:
                continue

        # lets write our failed stock list to text file for reference
        file_to_write = open('failed_symbols.txt', 'w')

        for symbol in MASTER_LIST_FAILED_SYMBOLS:
            file_to_write.write("%s\n" % symbol)

        print(datetime.datetime.now() - startTime)
    

if __name__ == "__main__":
    main()