import backtrader as bt
import backtrader.indicators as btind
import datetime
import psycopg2
import pandas as pd
import os

import q_credentials.db_risk_cred as db_risk_cred
import q_tools.write_to_db as write_to_db


class St(bt.Strategy):
    alias = 'Simple Strategy'
    params = dict(
        period=10,
        backtest=True
    )


    def log(self, arg):
        if not self.p.backtest:
            print('{} {}'.format(self.datetime.datetime(), arg))
        

    def __init__(self):
        self.ml_log = []
        self.db_run_id = None
        self.current_time=datetime.datetime.now()
        self.sma = [bt.indicators.SimpleMovingAverage(d, period=self.p.period) for d in self.datas]
        self.sma2 = [bt.indicators.SimpleMovingAverage(d, period=20) for d in self.datas]
        for i in self.sma:
            i.csv=True
        self.order = None
        self.buyprice = None
        self.buycomm = None
        # if arg:
        if self.p.backtest:
            self.datastatus = 1
        else:
            self.datastatus = 0
        self.conn = psycopg2.connect(host=db_risk_cred.dbHost , database=db_risk_cred.dbName, user=db_risk_cred.dbUser, password=db_risk_cred.dbPWD)

    def notify_data(self, data, status, *args, **kwargs):
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if status == data.LIVE:
            # self.counttostop = self.p.stopafter
            self.datastatus = 1

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.5f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.5f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.5f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))


    def save_down(self, input):
        if self.p.backtest and type(input) is dict:
            self.ml_log.append(input)
            # print('{} {}'.format(self.datetime.datetime(), arg))
        elif input=="EOS":
            ml_log_file = "ml_log.csv"
            # cur_path = os.path.dirname(os.path.abspath(__file__))
            df=pd.DataFrame(self.ml_log)
            df.to_csv(os.path.join(os.getcwd(),ml_log_file),index=False)

    def next(self):
        for i, d in enumerate(self.datas):
            dt, dn = self.datetime.datetime(), d._name
            pos = self.getposition(d).size
            # print('{} {} Position {}'.format(dt, dn, pos))
            self.save_down({'time':self.datetime.datetime(),'ticker':dn,'close':d.close[0],'sma1':self.sma[i][0],'sma2':self.sma2[i][0]})
            self.log('Price: {:.2f}, SMA: {}, Ticker:{}'.format(d.close[0],self.sma[0].PriceClose,dn))

            # if not pos:  # no market / no orders
            if self.datastatus:
                if d.close[0] > self.sma[i] and pos<=0:
                    self.order=self.close(data=d)
                    self.order=self.buy(data=d)
                    # print('{} {} Buy {}'.format(dt, dn, self.order.ref))
                    # self.log('BUY CREATE, %.5f - %s' % d.close[0] %d.name)
                    self.log('BUY CREATE {:.2f} at {}'.format(d.close[0],dn))

                elif d.close[0] < self.sma[i] and pos>=0:
                    self.order=self.close(data=d)
                    self.order=self.sell(data=d)
                    # print('{} {} Buy {}'.format(dt, dn, self.order.ref))
                    # self.log('BUY CREATE, %.5f' % d.close[0])
                    self.log('SELL CREATE {:.2f} at {}'.format(d.close[0],dn))

    def stop(self):
        if self.conn:
                self.conn.close()
        self.save_down("EOS")

    def start(self):
        print("Hello")
        # list(enumerate(self.getdatanames()))
        # self.getindicators()
        info_run_type = 'Backtest' if self.p.backtest else 'Live'
        info_tickers=','.join([d for d in (self.getdatanames())])
        info_indicators = ','.join([i.aliased for i in (self.getindicators())])
        info_timeframe = self.data0._timeframe # This is currently a number, have to change it later
        if self.p.backtest:
            info_start_date =  bt.num2date(self.data0.fromdate) # would have to change for live due to the backfill.
            info_end_date =  bt.num2date(self.data0.todate)
        else:
            info_start_date =  self.current_time # would have to change for live due to the backfill.
            info_end_date =  None

            info_end_date =None
        info_account = ""
        info_log_file = ""
        strat_info={'run_type':info_run_type,'recorded_time':self.current_time,'start_time':info_start_date,'end_time':info_end_date,
                    'strategy':self.alias,'tickers':info_tickers,'indicators':info_indicators,'frequency':info_timeframe,'account':info_account,'log_file':info_log_file}

        self.db_run_id=write_to_db.write_to_db(conn=self.conn, data_dict=strat_info, table='run_information',return_col='run_id')
