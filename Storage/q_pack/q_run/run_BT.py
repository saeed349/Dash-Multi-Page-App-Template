import argparse
import datetime
import glob
import os.path
import backtrader as bt
import boto3
import io
import pandas as pd
from sqlalchemy import create_engine
import psycopg2

import btoandav20
import pytz

import q_datafeeds.bt_datafeed_postgres as bt_datafeed_postgres
from q_strategies import *
import q_credentials.oanda_cred as oanda_cred
import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.db_indicator_cred as db_indicator_cred
# import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_analyzers.bt_strat_perform_analyzer as bt_strat_performance_analyzer
import q_analyzers.bt_pos_perform_analyzer as bt_pos_performance_analyzer
import q_analyzers.bt_transaction_analyzer as bt_trans_analyzer
import q_analyzers.bt_strategy_id_analyzer as bt_strategy_id_analyzer
import q_analyzers.bt_logger_analyzer as bt_logger_analyzer
import q_tools.args_parse_other as args_parse_other
import q_analyzers.bt_indicator_analyzer as bt_indicator_analyzer

def run(args=None): 
    if not args:
        args = parse_args(args)
        # args, unknown = parse_args.parse_known_args()


    cerebro = bt.Cerebro()

    # Data feed kwargs
    dkwargs = dict(**eval('dict(' + args.dargs + ')'))

    if args.load_symbol:
        s3 = boto3.client('s3',endpoint_url="http://minio-image:9000",aws_access_key_id="minio-image",aws_secret_access_key="minio-image-pass")
        Bucket="airflow-files"
        if args.universe=='US Equity':
            Key="interested_tickers_alpaca.xlsx"
        elif args.universe=='Forex':
            Key="interested_tickers_oanda.xlsx"
        elif args.universe=='Indian Equity':
            Key="interested_tickers_india.xlsx"
        read_file = s3.get_object(Bucket=Bucket, Key=Key)
        df = pd.read_excel(io.BytesIO(read_file['Body'].read()),sheet_name="d") #,sep=','
        ticker_list = list(df['Tickers'])
    else:
        ticker_list=args.tickers[0].split(',')
        print(ticker_list)

    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    if args.fromdate:
        fmt = dtfmt + tmfmt * ('T' in args.fromdate)
        dkwargs['fromdate'] = datetime.datetime.strptime(args.fromdate, fmt)    

    if args.todate:
        fmt = dtfmt + tmfmt * ('T' in args.todate)
        dkwargs['todate'] = datetime.datetime.strptime(args.todate, fmt)

    # cerebro.addanalyzer(bt_trans_analyzer.transactions_analyzer,_name='position_list')
    # cerebro.addanalyzer(bt_strategy_id_analyzer.strategy_id_analyzer,_name='strategy_id')
    # cerebro.addanalyzer(bt_strat_performance_analyzer.strat_performance_analyzer,_name='strat_perf')
    # cerebro.addanalyzer(bt_pos_performance_analyzer.pos_performance_analyzer,_name='pos_perf')
    conn_secmaster = psycopg2.connect(host=db_secmaster_cred.dbHost , database=db_secmaster_cred.dbName, user=db_secmaster_cred.dbUser, password=db_secmaster_cred.dbPWD)
    conn_indicator = psycopg2.connect(host=db_indicator_cred.dbHost , database=db_indicator_cred.dbName, user=db_indicator_cred.dbUser, password=db_indicator_cred.dbPWD)

    if args.ml_log:
        cerebro.addanalyzer(bt_logger_analyzer.logger_analyzer,_name='ml_logger')

    if args.load_indicator_db:
        cerebro.addanalyzer(bt_indicator_analyzer.indicator_analyzer,_name='indicator_db',conn_secmaster=conn_secmaster,conn_indicator=conn_indicator)

    if args.mode=='live':
        oandastore = btoandav20.stores.OandaV20Store(token=args.broker_token, account=args.broker_account, practice=True)
        for ticker in ticker_list:
            data = oandastore.getdata(dataname = ticker,timeframe = bt.TimeFrame.Minutes,compression=1,tz=pytz.timezone('US/Eastern'))
            cerebro.adddata(data)
        cerebro.broker = oandastore.getbroker()
        cerebro.addstrategy(globals()[args.strat_name].St, backtest=False)

    elif args.mode=='backtest':
        # conn = psycopg2.connect(host=db_secmaster_cred.dbHost , database=db_secmaster_cred.dbName, user=db_secmaster_cred.dbUser, password=db_secmaster_cred.dbPWD)
        # https://docs.sqlalchemy.org/en/13/core/pooling.html
        db_engine = create_engine('postgresql+psycopg2://'+db_secmaster_cred.dbUser+':'+ db_secmaster_cred.dbPWD +'@'+ db_secmaster_cred.dbHost +'/'+ db_secmaster_cred.dbName,pool_size=20,max_overflow=0)#,pool_size=10,max_overflow=10)
        conn = db_engine.connect()
        # print(dkwargs)
        for ticker in ticker_list:
            if args.timeframe == 'd':
                data = bt_datafeed_postgres.PostgreSQL_Historical(db=args.timeframe, conn=conn,ticker=ticker, name=ticker,**dkwargs) 
                cerebro.adddata(data)
            elif args.timeframe == 'w':
                data = bt_datafeed_postgres.PostgreSQL_Historical(db='d', conn=conn,ticker=ticker, name=ticker,**dkwargs) 
                cerebro.resampledata(data,timeframe = bt.TimeFrame.Weeks, compression = 1)
            elif args.timeframe == 'm':
                data = bt_datafeed_postgres.PostgreSQL_Historical(db='d', conn=conn,ticker=ticker, name=ticker,**dkwargs) 
                cerebro.resampledata(data,timeframe = bt.TimeFrame.Months, compression = 1)
            elif args.timeframe == 'h1':
                data = bt_datafeed_postgres.PostgreSQL_Historical(db=args.timeframe, conn=conn,ticker=ticker, name=ticker,**dkwargs,timeframe=bt.TimeFrame.Minutes, compression=60) 
                cerebro.adddata(data)
            elif args.timeframe == 'h4':
                data = bt_datafeed_postgres.PostgreSQL_Historical(db=args.timeframe, conn=conn,ticker=ticker, name=ticker,**dkwargs,timeframe=bt.TimeFrame.Minutes, compression=240)
                cerebro.adddata(data)
        # conn.close()
        db_engine.dispose()
        cerebro.broker.setcash(args.cash)
        cerebro.addstrategy(globals()[args.strat_name].St, **args.strat_param,conn_indicator=conn_indicator)
 

    cerebro.addsizer(bt.sizers.FixedSize, stake=1000)


    results = cerebro.run(tradehistory=True)  

    pnl = cerebro.broker.get_value() - args.cash
    print('Profit ... or Loss: {:.2f}'.format(pnl))

    strats = results
    if args.plot:
        cerebro.plot(style='candlestick',iplot=False,volume=False)
    
    conn_secmaster.close()
    conn_indicator.close()
    if conn:
        print("closing the stupid db connection")
        conn.close()

def parse_args(pargs=None):
    parser = argparse.ArgumentParser(   
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=('Rebalancing with the Conservative Formula'),
    )

    # parser.add_argument('--tickers', nargs='*' ,required=False,default=['AAPL,MSFT'], type=str, #['EUR_USD,GBP_USD'] #['PZZA'] #['BOM500010,BOM500034,BOM500087']
    #                     help='Pass the tickers with space')
    parser.add_argument('--tickers', nargs='*' ,required=False,default=['EUR_USD,GBP_USD'], type=str,  #['PZZA'] #['BOM500010,BOM500034,BOM500087']
                        help='Pass the tickers with space')
    
    parser.add_argument('--timeframe', required=False, default='daily',
                        help='Timeframe at whic the strategy needs to be run at')

    parser.add_argument('--dargs', default='',
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--fromdate', required=False, default='2015-7-1',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--cash', default=10000, type=float,
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--strat_name', required=False, default='simple_strategy_3', 
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--strat_param', required=False, default=dict(ml_serving='no',use_db='yes', use_level='yes'), #--strat_param "use_level=yes,use_db=yes,ml_serving=no"
                        action=args_parse_other.StoreDictKeyPair, metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--ml_log', required=False, default=False, type=args_parse_other.str2bool, const=True, nargs='?',
                        help='To save ML log or not')
    
    parser.add_argument('--mode', required=False, default='backtest',   
                        help='Live or Backtest')

    parser.add_argument('--broker_token', required=False, default=oanda_cred.token_practice,
                        help='Oanda Broker Token id')

    parser.add_argument('--broker_account', required=False, default=oanda_cred.acc_id_practice,
                        help='Oanda Broker Account id')

    parser.add_argument('--plot', required=False, default=False, type=args_parse_other.str2bool, const=True, nargs='?',
                    help='Plot the results')

    parser.add_argument('--load_indicator_db', required=False, default=True, type=args_parse_other.str2bool, const=True, nargs='?',
                    help='load the indicator data into DB')

    parser.add_argument('--load_symbol', required=False, default=False, type=args_parse_other.str2bool, const=True, nargs='?',
                    help='load the symbols from excel file')

    parser.add_argument('--universe', required=False, default='Forex',
                        help='Select the Universe - Currently US Equity, Forex Majors')

    # return parser.parse_args(pargs)
    args, unknown = parser.parse_known_args(pargs)
    return args



if __name__ == '__main__':
    run()


# python q_pack/q_run/run_BT.py --fromdate='2020-01-01' --todate='2020-06-01' --timeframe='1hour' --strat_param "use_level=yes,use_db=yes,ml_serving=no"