import backtrader as bt
import backtrader.indicators as btind
import datetime
import psycopg2
import pandas as pd
import os
import q_indicators.Candle_Pattern_Indicator as Candle_Pattern_Indicator
import q_indicators.Level_Indicator as Level_Indicator
import q_indicators.Level_Indicator_sr_plot as Level_Indicator_sr_plot
import q_indicators.Custom_Fractal as Custom_Fractal
import q_indicators.Anomaly_Indicator as Anomaly_Indicator
import mlflow.pyfunc
import q_credentials.db_indicator_cred as db_indicator_cred
class St(bt.Strategy):
    alias = 'Simple Strategy'
    params = dict(
        period=10,
        limdays=200,
        backtest=True,
        ml_serving=False,
        use_db=False,
        model_uri="24cbdab283244fac8d54405d58b2bbf1",
        use_level=True
    )


    def log(self, arg):
        # if not self.p.backtest:
        print('{} {}'.format(self.datetime.datetime(), arg))
        

    def __init__(self): 
        self.db_run_id = None
        self.conn_indicator = psycopg2.connect(host=db_indicator_cred.dbHost , database=db_indicator_cred.dbName, user=db_indicator_cred.dbUser, password=db_indicator_cred.dbPWD) 
        # self.rsi = [bt.indicators.RSI(d, period=30) for d in self.datas]

        # self.stoc = [bt.indicators.Stochastic(d, period=20) for d in self.datas]
        # self.atr = [bt.indicators.ATR(d, period=5) for d in self.datas]
        # for i in self.rsi:
        #     i.aliased='RSI'
        # for i in self.stoc:
        #     i.aliased='STOCHASTIC'
        # for i in self.atr:
        #     i.aliased='ATR'
        

        self.candle_1 = [Candle_Pattern_Indicator.Candle_Indicator(d,type=1) for d in self.datas]
        for i in self.candle_1:
            i.aliased='candle_1'
        self.candle_2 = [Candle_Pattern_Indicator.Candle_Indicator(d,type=2) for d in self.datas]
        for i in self.candle_2:
            i.aliased='candle_2'
        self.candle_3 = [Candle_Pattern_Indicator.Candle_Indicator(d,type=3) for d in self.datas]
        for i in self.candle_3:
            i.aliased='candle_3'
        self.anomaly_ind = [Anomaly_Indicator.Anomaly_Indicator(d) for d in self.datas]
        for i in self.anomaly_ind:
            i.aliased='anomaly'

        if self.p.use_level=='yes':
            # print("using level indicator")
            self.level_ind = [Level_Indicator.Level_Indicator(d,disp=True,use_db=True if self.p.use_db=='yes' else False,conn_indicator=self.conn_indicator) for d in self.datas]
            for i in self.level_ind:
                i.aliased='level'


        # self.level_plot_ind = [Level_Indicator_sr_plot.Level_Indicator(d,disp=False) for d in self.datas]
        # self.fractal_ind = [Custom_Fractal.Custom_Fractal(d) for d in self.datas]

        self.order = None
        self.buyprice = None
        self.buycomm = None
        # if arg:
        if self.p.backtest:
            self.datastatus = 1
        else:
            self.datastatus = 0

        if self.p.ml_serving=='yes':
            print("s3://mlflow-models/"+self.p.model_uri+"/artifacts/model")
            self.model_predict=mlflow.pyfunc.load_model(model_uri=("s3://mlflow-models/"+self.p.model_uri+"/artifacts/model"))


    def notify_data(self, data, status, *args, **kwargs):
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if status == data.LIVE:
            self.datastatus = 1

    
    def notify_order(self, order):        
        if (order.status>1): # 0 and 1 are created and submitted
            self.log('Order Status: {}: Ref: {}, Size: {}, Price: {}' \
                .format(order.Status[order.status], order.ref, order.size,
                        'NA' if not order.price else round(order.price,5)))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.5f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))



    def next(self): 
        for i, d in enumerate(self.datas):
            dt, dn = self.datetime.datetime(), d._name
            pos = self.getposition(d).size
            order_valid = datetime.timedelta(self.p.limdays)
            # print(d._name,'--time:',bt.num2date(d.datetime[0]),'--Open:',d.open[0],' High:',d.high[0],' Low:',d.low[0],' Close:',d.close[0])
            if self.datastatus and pos==0:
                # print(dn)
                # print(self.level_ind[i].Level[0])
                pass
                # print(self.candle_1[i].Highest[0],self.candle_1[i].Lowest[0])
                # if self.candle_1[i].Pattern>0:
                #     price_sl = self.candle_1[i].Lowest[0]-(self.atr[0])
                #     price_tp = self.candle_1[i].Highest[0]+(self.atr[0])
                #     self.order=self.buy_bracket(data=d,exectype=bt.Order.Market , stopprice=price_sl, limitprice=price_tp, valid=order_valid) #, valid=order_valid,price=None
                #     self.log('BUY CREATE {:.2f} at {}'.format(d.close[0],dn))
                # elif self.candle_1[i].Pattern<0:
                #     price_sl = self.candle_1[i].Highest[0]+(self.atr[0])
                #     price_tp = self.candle_1[i].Lowest[0]-(self.atr[0])
                #     self.order=self.sell_bracket(data=d,exectype=bt.Order.Market , stopprice=price_sl, limitprice=price_tp, valid=order_valid) #, valid=order_valid,price=None
                #     self.log('CSELL CREATE {:.2f} at {}'.format(d.close[0],dn))

    def stop(self):
        print("Strategy run finished with Run ID:",self.db_run_id)
        self.conn_indicator.close()
        # pd.DataFrame(self.level_ind[0].indicator_list).to_csv("level_indicator.csv")
        # df=pd.DataFrame(self.level_ind[0].indicator_list).to_csv("level_indicator.csv")

        # item['date_price'] for item in self.level_ind[0].indicator_list

        # df=pd.DataFrame.from_dict(self.level_ind[0].indicator_dict, orient='index')
        # df.to_csv("level_indicator.csv")
        # pd.DataFrame(self.level_ind[0].test_list).to_csv("indicator_file.csv")