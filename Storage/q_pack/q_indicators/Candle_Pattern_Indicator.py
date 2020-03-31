#-------------------TO-DO---------------------------#
# 1) Design a negligible range condition set as described in design choice (4): probably a function which takes in 
# the condition as parameter (<,=,>,<=,>=) and try ATR to define this range. The objective is to get the accuracy of visual
# proximity that humans make.
# 2) Redesign how "short" and "long" candles are taken, right now its the medium HL of last 5 including the one being tested.
# The most ideal would be an average of a bigger range.

# ------------------DESIGN CHOICE-------------------#
# 1) Will follow the same procedure as https://www.mql5.com/en/articles/101 and see if I am getting satisfiable results. 
# except for the part where we won't utilize the trend much (being agnostic of where(in uptrend or in downtrend) the patterns occur)
# 2) In the cal_candle_attr() easier conditions should be checked before stricter conditions like
# DOJI_SPINOFF needs to be checked before Doji and SPIN_TOP needs to be checked before Doji
# 3) Coulnd't identify much hammer and inv-hammer, originally it was .1, changed it .3 and still cant find many. So keeping it that way, to make sure
# I dont overfit to the data.
# 4) "Meeting Lines" double candlestick pattern, here the optimal condition is that the close of the 2 candlestics should be equal, but
# they will never be, so we need a range, since I am working with SBI data, the a price change of 2 is almost negligible, 
# so I need to find a negligible or reasonalble range like that. This is very important, because it later extends into other parts as well
# where the price won't exactly match or anything, but will be within an exceptable range, we have to define this acceptable range.
# 5) Making "long" and "short" a property of candle instead of a type
# 6) Generalizing common conditions, like if current candle is inside the previous candles body
# 7) Eventhough we need only 1 datasource to calculate the patterns, the plotting occurs in the space other than self.data. So it
# won't plot and therefore we need to use the base of the indicator as self.data 

import backtrader as bt
import numpy as np
import json

def frange(lower,upper,value):
    if (lower>upper):
        lower,upper=upper,lower
    if(value>=lower and value<=upper):
        return True
    else:
        return False

class Candle_Indicator(bt.Indicator):
    lines = ('Pattern','Highest','Lowest')
    plotlines = dict(Highest=dict(_plotskip='True'),
                     Lowest=dict(_plotskip='True'))

    params = (('type', 1),)
    
    def __init__(self):
        try:
            day_min=7*60
            time_dict={4:1,5:(day_min),6:(5*day_min),7:(23*day_min)}
            min_Tperiod=time_dict[self.data._timeframe]*self.data._compression
            max_Tperiod=time_dict[self.data._timeframe]*self.data._compression
            min_period=int((max_Tperiod*3)/min_Tperiod)
            print("Min period=",min_period)
            self.addminperiod(min_period)
        except:
            self.addminperiod(3)
        self.indicator_list=[]
        self.date_list=[]
    
    def calc_candle_attr(self,index=0):
        candle_dict={}
        candle_dict['high']=self.data.high[index]
        candle_dict['low']=self.data.low[index]
        candle_dict['close']=self.data.close[index]
        candle_dict['open']=self.data.open[index]
        
        candle_dict['side']='BULL' if candle_dict['open']<candle_dict['close'] else 'BEAR'
        candle_dict['body_size']=abs(candle_dict['open']-candle_dict['close'])
        candle_dict['shadow_low']=round((candle_dict['open']-candle_dict['low']) if candle_dict['side']=='BULL'  else \
                                                                 (candle_dict['close']-candle_dict['low']),3)
        candle_dict['shadow_high']=round((candle_dict['high']-candle_dict['close']) if candle_dict['side']=='BULL' else \
                                                                 (candle_dict['high']-candle_dict['open']),3)
        candle_dict['HL']=round(candle_dict['high']-candle_dict['low'],3)
        
        last_five_close = np.array(self.data.close.get(size=5))
        last_five_open = np.array(self.data.open.get(size=5))
        avg_OC=np.mean(abs(last_five_close-last_five_open))
        
        avg_close = np.median(np.array(self.data.close.get(size=5)))
        candle_dict['trend'] = "UPPER" if self.data.close[0]>avg_close else ("DOWN" if self.data.close[0]<avg_close else "LATERAL")
            
        candle_dict['long']=True if (candle_dict['body_size'] > avg_OC*2) else False
        candle_dict['short']=True if (candle_dict['body_size'] < avg_OC*0.5) else False
        
    
        candle_dict['type']=None
        
        candle_dict['type']="SPIN_TOP" if(candle_dict['shadow_low']>candle_dict['body_size'] and\
                                  candle_dict['shadow_high']>candle_dict['body_size']) \
                                  else candle_dict['type'] # instead of 1 time higher, maybe like 1.5 - needs testing
        
        candle_dict['type']="DOJI_SPINOFF" if(candle_dict['body_size']<(candle_dict['HL']*0.2)) \
                                           else candle_dict['type'] 
            
        candle_dict['type']="DOJI" if candle_dict['body_size']<(candle_dict['HL']*0.05) else candle_dict['type']
        
        if (candle_dict['shadow_low']<candle_dict['body_size']*0.1 and\
            candle_dict['shadow_high']<candle_dict['body_size']*0.1 and \
            candle_dict['body_size']>0):
            
            if(candle_dict['long']):
                candle_dict['type']="LONG_MARUBOZU"
            elif(candle_dict['short']=="SHORT"):
                candle_dict['type']="SHORT_MARUBOZU"
            else:
                candle_dict['type']="MARUBOZU"
        
        candle_dict['type']="HAMMER" if(candle_dict['shadow_low']>candle_dict['body_size']*2 and \
                                        candle_dict['shadow_high']<candle_dict['body_size']*0.3) else candle_dict['type']

        candle_dict['type']="INV_HAMMER" if(candle_dict['shadow_high']>candle_dict['body_size']*2 and \
                                            candle_dict['shadow_low']<candle_dict['body_size']*0.3) \
                                            else candle_dict['type']

        
        
        return candle_dict
    
    def next(self):
        pattern_name=""
        self.l.Pattern[0]=0 # this is to avoid the nan when writing to the db
        if self.params.type==1:
            candle_0=self.calc_candle_attr(0)
            if(candle_0['type']=="DOJI"):
                self.l.Pattern[0]=1
                pattern_name="DOJI"
            elif(candle_0['type']=="MARUBOZU"):
                self.l.Pattern[0]=2
                pattern_name="MARUBOZU"
            elif(candle_0['type']=="LONG_MARUBOZU"):
                self.l.Pattern[0]=2.5
                pattern_name="LONG_MARUBOZU"
            elif(candle_0['type']=="SHORT_MARUBOZU"):
                self.l.Pattern[0]=-2.5
                pattern_name="SHORT_MARUBOZU"
            elif(candle_0['type']=="HAMMER"):
                self.l.Pattern[0]=3 
                pattern_name="HAMMER"
            elif(candle_0['type']=="INV_HAMMER"):
                self.l.Pattern[0]=-3 
                pattern_name="INV_HAMMER"
            elif(candle_0['type']=="SPIN_TOP"):
                self.l.Pattern[0]=4 
                pattern_name="SPIN_TOP"
            elif(candle_0['type']=="DOJI_SPINOFF"):
                self.l.Pattern[0]=5
                pattern_name="DOJI_SPINOFF"
            elif(candle_0['long']):
                self.l.Pattern[0]=10
                pattern_name="long"
            elif(candle_0['short']):
                self.l.Pattern[0]=-10
                pattern_name="short"
            else:
                self.l.Pattern[0]=0
                pattern_name=""
            self.l.Highest[0] = candle_0['high']
            self.l.Lowest[0] = candle_0['low']

        elif self.params.type==2:
            candle_0=self.calc_candle_attr(0)
            candle_1=self.calc_candle_attr(-1)
            
            # if one candle lies inside the other
            zero_inside_one= True if(frange(lower=candle_1['open'],upper=candle_1['close'],value=candle_0['open']) and\
               frange(lower=candle_1['open'],upper=candle_1['close'],value=candle_0['close'])) else False
            one_inside_zero= True if(frange(lower=candle_0['open'],upper=candle_0['close'],value=candle_1['open']) and\
               frange(lower=candle_0['open'],upper=candle_0['close'],value=candle_1['close'])) else False
            
            if(candle_0['side']=="BULL" and candle_1['side']=="BEAR") and one_inside_zero:
                self.l.Pattern[0]=1 # BULLISH ENGULFING
                pattern_name="BULLISH ENGULFING"
            elif(candle_0['side']=="BEAR" and candle_1['side']=="BULL") and one_inside_zero:
                self.l.Pattern[0]=-1 # BEARISH ENGULFING
                pattern_name="BEARISH ENGULFING"
            elif zero_inside_one and (candle_1['side']=="BEAR"):
                if(candle_0['type']=="DOJI_SPINOFF" or candle_0['type']=="DOJI"):
                    self.l.Pattern[0]=2 # BULLISH HARAMI CROSS
                    pattern_name="BULLISH HARAMI CROSS"
                elif(candle_0['type']!="DOJI_SPINOFF" and candle_0['type']!="DOJI" and candle_0['side']=="BULL"):
                    self.l.Pattern[0]=3 # BULLISH HARAMI
                    pattern_name="BULLISH HARAMI"
            elif zero_inside_one and (candle_1['side']=="BULL"):
                if (candle_0['type']=="DOJI_SPINOFF" or candle_0['type']=="DOJI"):
                    self.l.Pattern[0]=-2 # BEARISH HARAMI CROSS
                    pattern_name="BEARISH HARAMI CROSS"
                elif(candle_0['type']!="DOJI_SPINOFF" or candle_0['type']!="DOJI"and candle_0['side']=="BEAR"):
                    self.l.Pattern[0]=-3 # BEARISH HARAMI  
                    pattern_name="BEARISH HARAMI  "              

            
            elif(not candle_0['short'] and not candle_1['short']\
            and (candle_0['side']=="BULL" and candle_1['side']=="BEAR")\
            and (candle_0['open']<candle_1['low'])\
            and (candle_0['close']<=candle_1['open'])\
            and (candle_0['close']>=candle_1['open']-(candle_1['body_size']/2))):
                self.l.Pattern[0]=4 # BULLISH (Piercing Pattern)
                pattern_name="BULLISH (Piercing Pattern)"
            elif(not candle_0['short'] and not candle_1['short']\
            and (candle_0['side']=="BEAR" and candle_1['side']=="BULL")\
            and (candle_0['open']>candle_1['high'])\
            and (candle_0['close']>=candle_1['open'])\
            and (candle_0['close']<=candle_1['close']-(candle_1['body_size']/2))):
                self.l.Pattern[0]=-4 # BEARISH (Dark Cloud Cover)
                pattern_name="BEARISH (Dark Cloud Cover)"
            
            elif(not candle_0['short'] and not candle_1['short']\
            and (candle_0['side']=="BULL" and candle_1['side']=="BEAR")\
            and (candle_0['open']<candle_1['low'])
            and (abs(candle_0['close']-candle_1['close'])<=2)):
                self.l.Pattern[0]=5 # BEARISH (Meeting Lines)
                pattern_name="BEARISH (Meeting Lines)"
            elif(not candle_0['short'] and not candle_1['short']\
            and (candle_0['side']=="BEAR" and candle_1['side']=="BULL")\
            and (candle_0['open']>candle_1['high']) and (abs(candle_0['close']-candle_1['close'])<=2)):
                self.l.Pattern[0]=-5 # BEARISH (Meeting Lines)
                pattern_name="BEARISH (Meeting Lines)"
            
            
            elif(candle_0['side']=="BEAR" and candle_1['side']=="BEAR")\
            and (candle_0['body_size']<candle_1['body_size']) and abs(candle_0['close']-candle_1['close'])<=2:
                 self.l.Pattern[0]=6 # BULLISH (Matching Low)
                 pattern_name="BULLISH (Matching Low)"
                    
            else:
                self.l.Pattern[0]=0
                pattern_name=""
            self.l.Highest[0] = max([candle_0['high'],candle_1['high']])
            self.l.Lowest[0] = min([candle_0['low'],candle_1['low']])

        elif self.params.type==3:
            candle_0=self.calc_candle_attr(0)
            candle_1=self.calc_candle_attr(-1)
            candle_2=self.calc_candle_attr(-2)
            
            # if open or close of the candles intersect each other
            zero_on_two = True if(frange(candle_2['open'],candle_2['close'],value=candle_0['open']) or 
                                 frange(candle_2['open'],candle_2['close'],value=candle_0['close'])) else False
            two_on_zero = True if(frange(candle_0['open'],candle_0['close'],value=candle_2['open']) or 
                                 frange(candle_0['open'],candle_0['close'],value=candle_2['close'])) else False
            
            if not candle_0['short'] and not candle_2['short']\
            and (zero_on_two or two_on_zero)\
            and (candle_1['type']=="DOJI_SPINOFF" or candle_1['type']=="DOJI")\
            and (not frange(max(candle_0['high'],candle_2['high']),min(candle_0['low'],candle_2['low']),value=candle_1['open'])):
                if(candle_0['side']=='BEAR' and candle_2['side']=='BULL'):
                    self.l.Pattern[0]=1 # BULLISH Abandoned Baby / Morning Doji Star
                    pattern_name="BULLISH Abandoned Baby"
                elif(candle_2['side']=='BEAR' and candle_0['side']=='BULL'):
                    self.l.Pattern[0]=-1 # BEARISH Abandoned Baby / Evening Doji Star
                    pattern_name="BEARISH Abandoned Baby"
                    
                    
            elif not candle_0['short'] and not candle_2['short']\
            and (zero_on_two or two_on_zero)\
            and (not frange(max(candle_0['high'],candle_2['high']),min(candle_0['low'],candle_2['low']),value=candle_1['open'])
                and not frange(max(candle_0['high'],candle_2['high']),min(candle_0['low'],candle_2['low']),value=candle_1['close'])):
                if(candle_0['side']=='BEAR' and candle_2['side']=='BULL'):
                    self.l.Pattern[0]=2 # BULLISH Morning Star
                    pattern_name="BULLISH Morning Star"
                elif(candle_2['side']=='BEAR' and candle_0['side']=='BULL'):
                    self.l.Pattern[0]=-2 # BEARISH Evening Star
                    pattern_name="BEARISH Evening Star"
                    

            elif not candle_0['short'] and not candle_1['short'] and not candle_2['short']\
            and candle_0['side']=="BULL" and candle_1['side']=="BULL" and candle_2['side']=="BULL"\
            and candle_0['close']>=candle_1['close'] and candle_1['close']>=candle_2['close']\
            and candle_0['open']>=candle_1['open'] and candle_1['open']>=candle_2['open']:
                self.l.Pattern[0]=3 # BULLISH Three White Soldiers
                pattern_name="BULLISH Three White Soldiers"
            
            elif not candle_0['short'] and not candle_1['short'] and not candle_2['short']\
            and candle_0['side']=="BEAR" and candle_1['side']=="BEAR" and candle_2['side']=="BEAR"\
            and candle_0['close']<=candle_1['close'] and candle_1['close']<=candle_2['close']\
            and candle_0['open']<=candle_1['open'] and candle_1['open']<=candle_2['open']:
                self.l.Pattern[0]=-3 # BEARISH Three Black Crows
                pattern_name="BEARISH Three Black Crows"

            else:
                self.l.Pattern[0]=0
                pattern_name=""

            self.l.Highest[0] = max([candle_0['high'],candle_1['high'],candle_2['high']])
            self.l.Lowest[0] = min([candle_0['low'],candle_1['low'],candle_2['low']])

        ind_dict={'level':self.l.Pattern[0],'pattern_name':pattern_name}
        self.indicator_list.append(json.dumps(ind_dict, indent=4, sort_keys=True, default=str))
        self.date_list.append(bt.num2date(self.data.datetime[0]))


