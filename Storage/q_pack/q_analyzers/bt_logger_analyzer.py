import backtrader as bt
import datetime


class logger_analyzer(bt.Analyzer):

    def get_analysis(self):

        return self.trades


    def __init__(self):

        self.trades = []


    def notify_trade(self, trade):
        print(self.data0[0])
