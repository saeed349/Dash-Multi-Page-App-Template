import backtrader as bt
import numpy as np
import json

import q_indicators.Candle_Pattern_Indicator as Candle_Pattern_Indicator

class Alpha_Indicator(bt.Indicator):
    lines = ('Pattern',)
    plotinfo = dict(subplot=False, plotlinelabels=False, plot=False)

    params = (('type', 1),)
    
    def __init__(self):
        # self.addminperiod(3)
        self.indicator_list=[]
        self.date_list=[]
        self.candle_pattern_ind=Candle_Pattern_Indicator.Candle_Indicator(self.data,type=2)
    
    def next(self):
        # pattern_name=""
        self.l.Pattern[0]=0 # this is to avoid the nan when writing to the db
        print("CANDLE PATTER=",self.candle_pattern_ind[0])
        if self.candle_pattern_ind[0]==1:
            self.l.Pattern[0]=1
        elif self.candle_pattern_ind[0]==-1:
            self.l.Pattern[0]=-1
        else:
            self.l.Pattern[0]=0

        ind_dict={'level':self.l.Pattern[0]}
        self.indicator_list.append(json.dumps(ind_dict, indent=4, sort_keys=True, default=str))
        self.date_list.append(bt.num2date(self.data.datetime[0]))

# import backtrader as bt


# class Alpha_Indicator(bt.ind.PeriodN):
#     '''
#     References:
#         [Ref 1] http://www.investopedia.com/articles/trading/06/fractals.asp
#     '''
#     lines = ('fractal_bearish', 'fractal_bullish')

#     plotinfo = dict(subplot=False, plotlinelabels=False, plot=True)

#     plotlines = dict(
#         fractal_bearish=dict(marker='^', markersize=4.0, color='black',
#                              fillstyle='full', ls=''),
#         fractal_bullish=dict(marker='v', markersize=4.0, color='blue',
#                              fillstyle='full', ls='')
#     )
#     params = (
#         ('period', 5),
#         ('bardist', 0.0001),  # distance to max/min in absolute perc
#         ('shift_to_potential_fractal', 2),
#     )

#     def next(self):
#         # A bearish turning point occurs when there is a pattern with the
#         # highest high in the middle and two lower highs on each side. [Ref 1]

#         last_five_highs = self.data.high.get(size=self.p.period)
#         max_val = max(last_five_highs)
#         max_idx = last_five_highs.index(max_val)

#         if max_idx == self.p.shift_to_potential_fractal:
#             self.lines.fractal_bearish[-2] = max_val * (1 + self.p.bardist)

#         # A bullish turning point occurs when there is a pattern with the
#         # lowest low in the middle and two higher lowers on each side. [Ref 1]
#         last_five_lows = self.data.low.get(size=self.p.period)
#         min_val = min(last_five_lows)
#         min_idx = last_five_lows.index(min_val)

#         if min_idx == self.p.shift_to_potential_fractal:
#             self.l.fractal_bullish[-2] = min_val * (1 - self.p.bardist)