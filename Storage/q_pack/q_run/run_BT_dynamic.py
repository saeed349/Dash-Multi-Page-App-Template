import q_run.run_BT as run_BT
import argparse
import q_tools.args_parse_other as args_parse_other
import q_credentials.oanda_cred as oanda_cred

def dag_function(list_ticker_list):
    for ticker_list in list_ticker_list:
        print(ticker_list)
        args=parse_args(fromdate='2016-1-1',tickers=ticker_list)
        print(args)
        run_BT.run(args)
        
def parse_args(fromdate='2016-1-1',tickers=['RELIANCE']):
    parser = argparse.ArgumentParser(   
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=('Rebalancing with the Conservative Formula'),
    )
    parser.add_argument('--tickers', nargs='*' ,required=False,default=tickers, type=str,  #['PZZA'] #['BOM500010,BOM500034,BOM500087']
                        help='Pass the tickers with space')
    
    parser.add_argument('--timeframe', required=False, default='d',
                        help='Timeframe at whic the strategy needs to be run at')

    parser.add_argument('--dargs', default='',
                        metavar='kwargs', help='kwargs in k1=v1,k2=v2 format')

    parser.add_argument('--fromdate', required=False, default=fromdate,
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
    args, unknown = parser.parse_known_args()
    return args