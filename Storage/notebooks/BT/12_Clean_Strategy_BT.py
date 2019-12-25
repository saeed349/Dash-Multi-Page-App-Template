####
# Multiple Symbols Live and Backtest with Oandav20
####

import argparse
import datetime
import glob
import os.path
import backtrader as bt

# import pyfolio as pf


import btoandav20

import pytz

from tabulate import tabulate

import q_datafeeds.bt_datafeed_postgres as bt_datafeed_postgres
import q_strategies.simple_strategy_2 as my_strats
import q_credentials.oanda_cred as oanda_cred
import q_credentials.db_secmaster_cred as db_cred
import q_analyzers.bt_perform_analyzer as bt_analyzers
import q_analyzers.bt_transaction_analyzer as bt_trans_analyzer
import q_analyzers.bt_strategy_id_analyzer as bt_strategy_id_analyzer
import q_analyzers.bt_logger_analyzer as bt_logger_analyzer

def run(args=None): 
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed kwargs
    dkwargs = dict(**eval('dict(' + args.dargs + ')'))

    # tickers = [itemfor item in args.tickers.split(',')]
    ticker_list = args.tickers.split(',')

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    if args.fromdate:
        fmt = dtfmt + tmfmt * ('T' in args.fromdate)
        dkwargs['fromdate'] = datetime.datetime.strptime(args.fromdate, fmt)

    if args.todate:
        fmt = dtfmt + tmfmt * ('T' in args.todate)
        dkwargs['todate'] = datetime.datetime.strptime(args.todate, fmt)

    cerebro.addanalyzer(bt_analyzers.trade_list, _name='performance_list')
    cerebro.addanalyzer(bt_trans_analyzer.transactions_analyzer,_name='position_list')
    # cerebro.addanalyzer(bt_logger_analyzer.logger_analyzer,_name='logger_writing') # this is for logging, not using at the moment
    cerebro.addanalyzer(bt_strategy_id_analyzer.strategy_id_analyzer,_name='strategy_id')
    cerebro.addanalyzer(bt_logger_analyzer.logger_analyzer,_name='ml_logger')



    # necessary database info to connect
    if args.live:
        oandastore = btoandav20.stores.OandaV20Store(token=oanda_cred.token_practice, account=oanda_cred.acc_id_practice, practice=True)
        for ticker in ticker_list:
            data = oandastore.getdata(dataname = ticker,timeframe = bt.TimeFrame.Minutes,compression=1,tz=pytz.timezone('US/Eastern'))#,fromdate = datetime.datetime(2019,10,15)
            cerebro.adddata(data)
        cerebro.broker = oandastore.getbroker()
        cerebro.addstrategy(my_strats.St, backtest=False)

    elif not args.live:

        for ticker in ticker_list:
            data = bt_datafeed_postgres.PostgreSQL_Daily(dbHost=db_cred.dbHost,dbUser=db_cred.dbUser,dbPWD=db_cred.dbPWD,dbName=db_cred.dbName,ticker=ticker, name=ticker,**dkwargs)
            cerebro.adddata(data)
        cerebro.broker.setcash(args.cash)
        cerebro.addstrategy(my_strats.St, **eval('dict(' + args.strat + ')'))
 
    

    cerebro.addsizer(bt.sizers.FixedSize, stake=1000)


    results = cerebro.run(tradehistory=True)  # execute it all
    # results = cerebro.run()

    # Basic performance evaluation ... final value ... minus starting cash
    pnl = cerebro.broker.get_value() - args.cash
    print('Profit ... or Loss: {:.2f}'.format(pnl))

    strats = results
    cerebro.plot(style='candlestick',iplot=False,volume=False)
    # trade_list = strats[0].analyzers.position_list.get_analysis()
    # print (tabulate(trade_list, headers="keys"))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=('Rebalancing with the Conservative Formula'),
    )

    parser.add_argument('--tickers', nargs='*' ,required=False,default='EUR_USD', type=str, #,GBP_USD,USD_JPY
                        help='Pass the tickers with space')

    parser.add_argument('--dargs', default='',
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='2010-1-1',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='2019-7-30',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--cash', default=10000, type=float,
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--strat', required=False, default='ml_log=True,ml_serving=True', # backtest=False
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')
    
    parser.add_argument('--live', required=False, default=False,
                        help='Live or Backtest')


    return parser.parse_args(pargs)


if __name__ == '__main__':
    run()

