
import backtrader as bt
import numpy as np
import json

class Anomaly_Indicator(bt.Indicator):
    lines = ('vol_anomaly', 'vol_anomaly_2','gap_signal')
    # lines = ('test',)
    params = (('period_ema', 10),)
    # plotlines = dict(vol_anomaly=dict(_plotskip='True'),
    #                  vol_anomaly_trend_2=dict(_plotskip='True'),
    #                  gap_signal=dict(_plotskip='True'))
    
    def __init__(self):
        self.addminperiod(3)
        self.ind_dict={}
        self.ind_dict['bull'] = bt.If(self.data.close > self.data.open, 1, 0)
        self.ind_dict['bear'] = bt.If(self.data.close < self.data.open, 1, 0)
        self.ind_dict['body_size'] = abs(self.data.close-self.data.open)
        self.ind_dict['body_size_ema'] = bt.indicators.EMA(self.ind_dict['body_size'], period=self.p.period_ema)
        self.ind_dict['body_size_dev'] = abs(self.ind_dict['body_size']-self.ind_dict['body_size_ema'])/self.ind_dict['body_size_ema']

        self.ind_dict['vol_ema'] = bt.indicators.EMA(self.data.volume, period=self.p.period_ema)
        self.ind_dict['vol_dev'] = abs(self.data.volume-self.ind_dict['vol_ema'])/self.ind_dict['vol_ema']
        self.ind_dict['vol_anomaly'] = self.ind_dict['body_size_dev'] * (1 - self.ind_dict['vol_dev'])
        self.ind_dict['vol_anomaly'] = bt.If(self.ind_dict['vol_anomaly'] < 0, 0, self.ind_dict['vol_anomaly'])
        
        self.ind_dict['gap'] = self.data.open(0)-self.data.close(-1)
        self.ind_dict['gap_ema'] = bt.indicators.EMA(abs(self.ind_dict['gap']), period=self.p.period_ema)
        self.ind_dict['gap_dev'] = (abs(self.ind_dict['gap'])-self.ind_dict['gap_ema'])/self.ind_dict['gap_ema']
        self.ind_dict['gap_signal'] = bt.If(self.ind_dict['gap_dev'] < 0, 0, self.ind_dict['gap_dev'])
        self.ind_dict['gap_signal'] = bt.If(self.ind_dict['gap'] < 0, (self.ind_dict['gap_signal']*-1),self.ind_dict['gap_signal']) # assigning sign

        self.ind_dict['wick_bull'] = bt.If(self.data.open > self.data.close, self.data.high - self.data.open, self.data.high - self.data.close) 
        self.ind_dict['wick_bear'] = bt.If(self.data.open > self.data.close, self.data.close - self.data.low, self.data.open - self.data.low)
        self.ind_dict['wick_bull_ema'] = bt.indicators.EMA(self.ind_dict['wick_bull'], period=self.p.period_ema)
        self.ind_dict['wick_bear_ema'] = bt.indicators.EMA(self.ind_dict['wick_bear'], period=self.p.period_ema)
        self.ind_dict['wick_bull_dev'] = (abs(self.ind_dict['wick_bull'])-self.ind_dict['wick_bull_ema'])/self.ind_dict['wick_bull_ema']
        self.ind_dict['wick_bear_dev'] = (abs(self.ind_dict['wick_bear'])-self.ind_dict['wick_bear_ema'])/self.ind_dict['wick_bear_ema']
        self.ind_dict['wick_bull_signal'] = bt.If(self.ind_dict['wick_bull_dev'] < 0, 0, self.ind_dict['wick_bull_dev'])
        self.ind_dict['wick_bear_signal'] = bt.If(self.ind_dict['wick_bear_dev'] < 0, 0, self.ind_dict['wick_bear_dev'])
 
        cond_volume_bull = bt.If(self.data.volume(0)>self.data.volume(-1),1,0)
        cond_volume_bear = bt.If(self.data.volume(0)<self.data.volume(-1),1,0)
        cond_body_bull = bt.If(self.ind_dict['body_size'](0)>self.ind_dict['body_size'](-1),1,0)
        cond_body_bear = bt.If(self.ind_dict['body_size'](0)<self.ind_dict['body_size'](-1),1,0)
        cond_same_candle = bt.If((self.ind_dict['bull'](0)==self.ind_dict['bull'](-1)),1,0)
        condition=(cond_volume_bear * cond_body_bull * cond_same_candle * self.ind_dict['bull']) + (cond_volume_bull * cond_body_bear * cond_same_candle * self.ind_dict['bear'])
        self.ind_dict['vol_anomaly_2'] = bt.If (condition==1, 1, 0)

        self.l.vol_anomaly=self.ind_dict['vol_anomaly']
        self.l.vol_anomaly_2=self.ind_dict['vol_anomaly_2']
        self.l.gap_signal=self.ind_dict['gap_signal']

        # self.ind_dict['date_price']=self.data.datetime
        self.indicator_list=[]
        self.date_list=[]

        # I am not doing the  Anomaly where a rising candle with falling volume and vice versa for 3 candles now  
        # cond_volume_bull=((df['volume']>df['volume'].shift(1))&(df['volume'].shift(1)>df['volume'].shift(2))) 
        # cond_volume_bear=((df['volume']<df['volume'].shift(1))&(df['volume'].shift(1)<df['volume'].shift(2))) 
        # cond_body_bull=((df['body_size']>df['body_size'].shift(1))&(df['body_size'].shift(1)>df['body_size'].shift(2)))
        # cond_body_bear=((df['body_size']<df['body_size'].shift(1))&(df['body_size'].shift(1)<df['body_size'].shift(2)))
        # # using these weird formulas because of the nans created by shift
        # cond_same_candle_bull=(df['bull']==df['bull'].shift(1))&(df['bull'].shift(1)==df['bull'].shift(2)) & df['bull']
        # cond_same_candle_bear=(df['bull']==df['bull'].shift(1))&(df['bull'].shift(1)==df['bull'].shift(2)) & ~df['bull']
        # condition=(cond_volume_bear & cond_body_bull & cond_same_candle_bull) | (cond_volume_bull & cond_body_bear & cond_same_candle_bear)

    def next(self):
        temp_dict=dict(zip(self.ind_dict.keys(),[v[0] for v in self.ind_dict.values()]))
        self.indicator_list.append(json.dumps(temp_dict, indent=4, sort_keys=True, default=str))
        self.date_list.append(bt.num2date(self.data.datetime[0]))
