###############################################################################
# Author: Saeed Rahman
# Date: 8/21/2019
# A simple SMA Strtategy to Backtest FX Strategy
###############################################################################

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
from datetime import datetime  
import cred
import btoandav20
import pytz
#Oanda Account Info
api_key = cred.token_prac
account_number = cred.acc_id_prac


# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 45),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        tm= self.datas[0].datetime.time(0)
        # print('%s, %s' % (dt.isoformat(), txt))
        print(dt," ", tm," ",txt)

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)

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

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.5f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        print(datetime.now())
        # Simply log the closing price of the series from the reference
        self.log('Close, %.5f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0]:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.5f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:

            if self.dataclose[0] < self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.5f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

    def notify_data(self, data, status, *args, **kwargs):

        if status == data.LIVE:  # the data has switched to live data
           # do something
           pass

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

    
    oandastore = btoandav20.stores.OandaV20Store(token=api_key, account=account_number, practice=True)

    cerebro.broker = oandastore.getbroker()

    data = oandastore.getdata(
        dataname = "EUR_USD",
        timeframe = bt.TimeFrame.Minutes,
        compression=1,tz=pytz.timezone('US/Eastern')
        # backfill_start=False, backfill=False
        # compression = 30,
        # fromdate = datetime(2018,11,1),
        # todate=datetime(2019,6,30)
        )

    # Add data
    cerebro.adddata(data)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    cerebro.run()

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=1)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())