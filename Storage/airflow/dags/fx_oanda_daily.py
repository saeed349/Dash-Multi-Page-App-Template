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
import cred
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import oandapyV20.endpoints.accounts as accounts
import oandapyV20

MASTER_LIST_FAILED_SYMBOLS = []

def load_db_credential_info(f_name_path):
    """
    load text file holding our database credential info and the database name
    args:
        f_name_path: name of file preceded with "\\", type string
    returns:
        array of 4 values that should match text file info
    """
    cur_path = os.getcwd()
    # lets load our database credentials and info
    f = open(cur_path + f_name_path, 'r')
    lines = f.readlines()[1:]
    lines = lines[0].split(',')
    return lines
    
def obtain_list_db_tickers(conn):
    """
    query our Postgres database table 'symbol' for a list of all tickers in our symbol table
    args:
        conn: a Postgres DB connection object
    returns: 
        list of tuples
    """
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT id, ticker FROM symbol")
        data = cur.fetchall()
        return [(d[0], d[1]) for d in data]

def fetch_vendor_id(vendor_name, conn):
    """
    Retrieve our vendor id from our PostgreSQL DB, table data_vendor.
    args:
        vendor_name: name of our vendor, type string.
        conn: a Postgres DB connection object
    return:
        vendor id as integer
    """
    cur = conn.cursor()
    cur.execute("SELECT id FROM data_vendor WHERE name = %s", (vendor_name,))
    # will return a list of tuples
    vendor_id = cur.fetchall()
    # index to our first tuple and our first value
    vendor_id = vendor_id[0][0]
    return vendor_id


def load_data(symbol, symbol_id, vendor_id, conn, start_date):
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
    accountID=cred.acc_id_prac
    access_token=cred.token_prac
    api = oandapyV20.API(access_token=access_token)
    client = oandapyV20.API(access_token=access_token)

    cur = conn.cursor()
    end_dt = datetime.datetime.now()
    
    try:
        data = oanda_historical_data(instrument=symbol,start_date=start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),end_date=end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),client=client)
        # data = yf.download(symbol, start=start_dt, end=end_dt)
    except:
        MASTER_LIST_FAILED_SYMBOLS.append(symbol)
        raise Exception('Failed to load {}'.format(symbol))

    if data.empty:
        print(symbol," already updated")

    else:        
        # create new dataframe matching our table schema
        # and re-arrange our dataframe to match our database table
        columns_table_order = ['data_vendor_id', 'stock_id', 'created_date', 
                               'last_updated_date', 'date_price', 'open_price',
                               'high_price', 'low_price', 'close_price', 'volume']
        newDF = pd.DataFrame()
        newDF['date_price'] =  data.index
        data.reset_index(drop=True,inplace=True)
        newDF['open_price'] = data['open']
        newDF['high_price'] = data['high']
        newDF['low_price'] = data['low']
        newDF['close_price'] = data['close']
        newDF['volume'] = data['volume']
        newDF['stock_id'] = symbol_id
        newDF['data_vendor_id'] = vendor_id
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
                        INSERT INTO daily_data (data_vendor_id, stock_id, created_date,
                        last_updated_date, date_price, open_price, high_price, low_price, close_price, volume) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
        cur.executemany(insert_query, tuples_mkt_data)
        conn.commit()    
        print('{} complete!'.format(symbol))


def oanda_historical_data(instrument,start_date,end_date,granularity='D',client=None):
    params = {
    "from": start_date,
    "to": end_date,
    "granularity": granularity,
    "count": 2500,
    }

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

def main():

    initial_start_date = datetime.datetime(2010,12,30)
    
    db_info_file = "database_info.txt"
    db_info_file_p = "/dags/" + db_info_file
    # necessary database info to connect
    db_host, db_user, db_password, db_name = load_db_credential_info(db_info_file_p)

    # connect to our securities_master database
    conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)

    # vendor name for Yahoo
    vendor = 'Oanda'
    vendor_id = fetch_vendor_id(vendor, conn)


    ticker_info_file = "interested_tickers.xlsx"
    ticker_info_file_p = "/dags/" + ticker_info_file
    cur_path = os.getcwd()
    f = cur_path + ticker_info_file_p
    df_tickers=pd.read_excel(f,sheet_name='daily')

    if df_tickers.empty:
        print("Empty Ticker List")
    else:
        # Getting the last date for each interested tickers
        sql="""select a.last_date, b.id as stock_id, b.ticker from
            (select max(date_price) as last_date, stock_id
            from daily_data 
            group by stock_id) a right join symbol b on a.stock_id = b.id 
            where b.ticker in {}""".format(tuple(df_tickers['Tickers'])).replace(",)", ")")
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
                load_data(symbol, symbol_id, vendor_id, conn, start_date=last_date)
            except:
                continue

        # lets write our failed stock list to text file for reference
        file_to_write = open('failed_symbols.txt', 'w')

        for symbol in MASTER_LIST_FAILED_SYMBOLS:
            file_to_write.write("%s\n" % symbol)

        print(datetime.datetime.now() - startTime)
    

if __name__ == "__main__":
    main()