import backtrader as bt
import backtrader.indicators as btind
import datetime
import psycopg2
import pandas as pd
import os
import q_indicators.Alpha_Indicator as Alpha_Indicator
import q_credentials.db_indicator_cred as db_indicator_cred
import q_indicators.Candle_Pattern_Indicator as Candle_Pattern_Indicator
import q_indicators.Level_Indicator as Level_Indicator
import q_indicators.Level_Indicator_sr_plot as Level_Indicator_sr_plot
import q_indicators.Anomaly_Indicator as Anomaly_Indicator
class St(bt.Strategy):
    alias = 'Simple Strategy'
    params = dict(
        period=10,
        limdays=200,
        backtest=True,
        ml_serving=False,
        use_db=False,
        model_uri="24cbdab283244fac8d54405d58b2bbf1",
        use_level=True,
        conn_indicator=None
    )


    def log(self, arg):
        # if not self.p.backtest:
        print('{} {}'.format(self.datetime.datetime(), arg))
        

    def __init__(self): 
        self.db_run_id = None

        # self.alpha_ind = [Alpha_Indicator.Alpha_Indicator(d) for d in self.datas]
        # for i in self.alpha_ind:
        #     i.aliased='alpa_ind'
        
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

        self.cash_at_start=self.broker.cash

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
            # if not order.Status[order.status] in (['Accepted','Completed','Canceled']):
            self.log('--------Order Status: {}: Ref: {}, Size: {}, Price: {}, Cash {}' \
                .format(order.Status[order.status], order.ref, order.size,
                        'NA' if not order.price else round(order.price,5),int(self.broker.cash)))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.5f, NET %.2f for %.1f' %
                 (trade.pnl, trade.pnlcomm,trade.ref))



    def next(self): 
        for i, d in enumerate(self.datas):
            dt, dn = self.datetime.datetime(), d._name
            pos = self.getposition(d).size
            order_valid = datetime.timedelta(self.p.limdays)
            # print(d._name,'--time:',bt.num2date(d.datetime[0]),'--Open:',d.open[0],' High:',d.high[0],' Low:',d.low[0],' Close:',d.close[0])
            # if self.datastatus and pos==0:
            if self.datastatus:
                # print(dn)
                # print(self.level_ind[i].Level[0])
                # pass
                # print(self.candle_1[i].Highest[0],self.candle_1[i].Lowest[0])
                sl_percent=0.02
                available_cash=self.cash_at_start/10 #ideally it should be self.broker.cash which shows the available cash
                if self.candle_2[i].Pattern==1:
                    price_sl = self.candle_2[i].Lowest[0]#-(self.atr[0])2
                    price_tp = d.close[0]+2*(d.close[0]-price_sl)#-self.candle_2[i].Highest[0]#+(self.atr[0])
                    quant= int((available_cash*sl_percent)/(d.close[0]-price_sl))
                    self.order=self.buy_bracket(size=quant,data=d,exectype=bt.Order.Market , stopprice=price_sl, limitprice=price_tp, valid=order_valid) #, valid=order_valid,price=None
                    self.log('{}, BUY CREATE {:.2f} at {} with SL:{:.2f} and TP:{:.2f}'.format(quant,d.close[0],dn,price_sl,price_tp))
                elif self.candle_2[i].Pattern==-1:
                    price_sl = self.candle_2[i].Highest[0]#+(self.atr[0])
                    price_tp = d.close[0]-2*(price_sl-d.close[0])#self.candle_2[i].Lowest[0]#-(self.atr[0])
                    quant=int((available_cash*sl_percent)/(price_sl-d.close[0]))
                    self.order=self.sell_bracket(size=-quant,data=d,exectype=bt.Order.Market , stopprice=price_sl, limitprice=price_tp, valid=order_valid) #, valid=order_valid,price=None
                    self.log('{}, SELL CREATE {:.2f} at {} with SL:{:.2f} and TP:{:.2f}'.format(quant,d.close[0],dn,price_sl,price_tp))
    def stop(self):
        print("Strategy run finished with Run ID:",self.db_run_id)
        # self.p.conn_indicator.close()
        # pd.DataFrame(self.level_ind[0].indicator_list).to_csv("level_indicator.csv")
        # df=pd.DataFrame(self.level_ind[0].indicator_list).to_csv("level_indicator.csv")

        # item['date_price'] for item in self.level_ind[0].indicator_list

        # df=pd.DataFrame.from_dict(self.level_ind[0].indicator_dict, orient='index')
        # df.to_csv("level_indicator.csv")
        # pd.DataFrame(self.level_ind[0].test_list).to_csv("indicator_file.csv")