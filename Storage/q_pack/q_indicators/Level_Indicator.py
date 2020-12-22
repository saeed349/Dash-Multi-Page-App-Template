#-------------------TO-DO---------------------------#
# 1) Optimize the indicator, right now it takes too around 22 seconds to run this, it shouldn't. The main reason being, number of 
#    loops. You can put all the level creation and testing in one single loop that will loop until the maximum length of all 4 levels list
#    Easier said than done, this will create a lot of problems for sure, so test it out extensively with and without under different 
#    scenarios before making the change.

# ------------------DESIGN CHOICE-------------------#
# 1) Seperating the merging of new vs original levels, this is because if we merge them, then we loose the identity of new,
#    which means that they would never be void (persistence problem)
# 2) Reversing the index of new levels, because when support[low, close] becomes new_resistance, we have to check that future prices
#    don't go above close not low, so we reverse it into the format of resistance [close, low] ([high price,low price] like resistance)
# 3) Minperiod - the indicator analysis would only start working when there is atleast 5 historical candles from the get method
#    Minperiod - since we have 2 datasources, we need to make sure there are enough lessfrequent datapoints in the minperiods
# 4) Instead of using an extra parameter to decide whether which data for calculating levels and which data to check the calculated levels
#    we are deciding it based on the number of data's the indicator is getting, if it gets 2 sources, then we initialize these into 
#    2 new class variables self.data and self.data. If only 1 data is available both of these new variables will point to 
#    self.data. This way if only data is passed the levels would be calculated on this and the checking will also happen with this data.
# 5) In the strategy once we are inside a particular level range, then we need the level range to set the right SL and TP
#    therefore we add these 2 new class variables self.in_res_range & self.in_sup_range. 
# 6) support and new_support don't merge as stated in (1). But inside the strategy we need the merged level.
# New
# 7) Instead of looking for whether the current datetime is in the dataframe from the DB, I would rather look if the datetime is before
#    the last date in the dataframe, this is to avoid the situation where we have data in the DB for 2015 to 2018, and we are quering for 2014
#    if the indicator is quering for an old value then it should be in the DB. And the calculation should only happen for the latest values.

# ------------------FUTURE WORK-------------------#
# 1) Loading the data from the DB
#    First the data would be loaded in the init for the indicator and for the security. After that in the next you would compare the current datetime with the 
#    latest datetime in the dataframe, if its falls under that then use the value from dataframe for the lines otherwise perform the calculations.
#    While getting the list of support and resistance from the DB, the datetime object would be in string, convert it using the below code.
        # sql="""select * from daily_data"""
        # df_ind=pd.read_sql(sql,con=conn)
        # test=df_ind.merge(df_ind['value'].apply(pd.Series), left_index=True, right_index=True)
        # # another way
        # test=pd.concat([df_ind.drop(['value'], axis=1), df_ind['value'].apply(pd.Series)], axis=1)
        # test_list=test['support'][200]
        # [[ls[0],ls[1],datetime.strptime(ls[2],'%Y-%m-%d %H:%M:%S'),ls[3]] for ls in test_list]



import datetime # can remove, added for testing

import backtrader as bt
import itertools
import numpy as np 
import pandas as pd
import json
import psycopg2

import q_credentials.db_indicator_cred as db_indicator_cred
import q_tools.read_db as read_db


def frange(lower,upper,value):
    if (lower>upper):
        lower,upper=upper,lower
    
    if(value>=lower and value<=upper):
        return True
    else:
        return False

# Take a combination of 2 of a list of levels that we get and combine it. 
# The before_length and after_length is a neat trick where u exit this function if before and after merging the number of layers are the same
def merging_levels(level,support=True):
    before_length=0
    after_length=1
    while(before_length!=after_length):
        comb_list=list(itertools.combinations(level,2))
        before_length=len(level)
        ind = 0 if support else 1
        for each in comb_list:
            # the 2 if's are for checking if support1 falls in range of support2 or vice versa
            level1=each[0]
            level2=each[1]
            if ~level1[-1] or ~level2[-1]:
                # print(level1,level2)
                after_length=len(level)
                continue

            if(frange(level1[0],level1[1],value=level2[ind])): # checks if the value falls in the range of other two
                merged_level=[min(level1[0],level2[0]),max(level1[1],level2[1]),min(level1[2],level2[2]),(level1[3]&level2[3]),False] if support else\
                         [max(level1[0],level2[0]),min(level1[1],level2[1]),min(level1[2],level2[2]),(level1[3]&level2[3]),False]                
                level.append(merged_level) # add the new support 
                # the below ifelse logic is keep the newly formed level and remove the modified level(S/R to R/S) whenever the combination involves a mixture of 2
                if (~level1[3] & level2[3]):
                    level.remove(level1)
                elif (level1[3] & ~level2[3]):
                    level.remove(level2)
                else:
                    level.remove(level1)
                    level.remove(level2)
                after_length=len(level) # updating the change in length
                break # now it will go back to the for loop and there will be a change in length
            elif(frange(level2[0],level2[1],value=level1[ind])):
                merged_level=[min(level1[0],level2[0]),max(level1[1],level2[1]),min(level1[2],level2[2]),(level1[3]&level2[3]),False] if support else \
                         [max(level1[0],level2[0]),min(level1[1],level2[1]),min(level1[2],level2[2]),(level1[3]&level2[3]),False]
                level.append(merged_level)
                if (~level1[3] & level2[3]):
                    level.remove(level1)
                elif (level1[3] & ~level2[3]):
                    level.remove(level2)
                else:
                    level.remove(level1)
                    level.remove(level2)
                after_length=len(level)
                break
            else:
                after_length=len(level) 
                # now the length would be same, but its not breaking yet, so we'll again go over all the combinations 
#         print(before_length,after_length)
    return level

class Level_Indicator(bt.Indicator):

    lines = ('level',)
    # lines = ('Level','s_out','r_out','s_in','r_in')
     
    # plotinfo = dict(subplot=True)
    plotinfo = dict(subplot=True)
    
    # plotlines = dict(s_out=dict(color='green'),
    #                     r_out=dict(color='red'),
    #                     s_in=dict(color='green'),
    #                     r_in=dict(color='red'))

    params = (
    ('disp',False),
    ('use_db',False), #True
    ('conn_indicator',None),
    ('period_ema_wick', 30)
    )

    
    def __init__(self):

        self.ind_dict={}

        # this is for identifying those really big 
        self.ind_dict['wick_bull'] = bt.If(self.data.open > self.data.close, self.data.high - self.data.open, self.data.high - self.data.close) 
        self.ind_dict['wick_bear'] = bt.If(self.data.open > self.data.close, self.data.close - self.data.low, self.data.open - self.data.low)
        self.ind_dict['wick_bull_ema'] = bt.indicators.EMA(self.ind_dict['wick_bull'], period=self.p.period_ema_wick)
        self.ind_dict['wick_bear_ema'] = bt.indicators.EMA(self.ind_dict['wick_bear'], period=self.p.period_ema_wick)
        self.ind_dict['wick_bull_dev'] = (abs(self.ind_dict['wick_bull'])-self.ind_dict['wick_bull_ema'])/self.ind_dict['wick_bull_ema']
        self.ind_dict['wick_bear_dev'] = (abs(self.ind_dict['wick_bear'])-self.ind_dict['wick_bear_ema'])/self.ind_dict['wick_bear_ema']
        # self.ind_dict['wick_bull_signal'] = bt.If(self.ind_dict['wick_bull_dev'] < 0, 0, self.ind_dict['wick_bull_dev'])
        # self.ind_dict['wick_bear_signal'] = bt.If(self.ind_dict['wick_bear_dev'] < 0, 0, self.ind_dict['wick_bear_dev'])

        day_min=7*60
        time_dict={4:1,5:day_min,6:(5*day_min),7:(23*day_min)}
        min_Tperiod=time_dict[self.data._timeframe]*self.data._compression
        max_Tperiod=time_dict[self.data._timeframe]*self.data._compression
        min_period=int((max_Tperiod*1)/min_Tperiod)
        # print("Min period=",min_period)
        self.addminperiod(min_period+1)      
        self.atr = bt.indicators.ATR(self.data, period=5)
        self.level = {'support':[],
                     'resistance':[]
                     }
        self.indicator_list=[]
        self.date_list=[]

        self.test_list=[] # remove this 

        # for plotting and checking purposes
        # self.in_res_range=0
        # self.in_sup_range=0
        self.latest_db_date = datetime.datetime(2000, 1, 1)
        self.indicator_df = pd.DataFrame()
        # self.p.conn_indicator = psycopg2.connect(host=db_indicator_cred.dbHost , database=db_indicator_cred.dbName, user=db_indicator_cred.dbUser, password=db_indicator_cred.dbPWD)     
        sec_name=self.data._name 
        if self.params.use_db:
            try:
                ind_name='level'
                sql="SELECT id FROM symbol WHERE ticker = '"+sec_name+"'"
                symbol_id=read_db.read_db_single(sql,self.p.conn_indicator)
                sql="SELECT id FROM indicator WHERE name = '"+ind_name+"'"
                ind_id=read_db.read_db_single(sql,self.p.conn_indicator)   
                sql="SELECT date_price, value FROM daily_data WHERE indicator_id = %s and symbol_id = %s" %(ind_id, symbol_id)
                self.indicator_df=pd.read_sql(sql,self.p.conn_indicator) 
                self.indicator_df.set_index('date_price',inplace=True)
                self.indicator_df=pd.concat([self.indicator_df.drop(['value'], axis=1), self.indicator_df['value'].apply(pd.Series)], axis=1)
                print("got data")
                self.latest_db_date=self.indicator_df.index.max()
                self.level['support'] = [[ls[0],ls[1],datetime.datetime.strptime(ls[2],'%Y-%m-%d %H:%M:%S'),ls[3]] for ls in self.indicator_df.iloc[-1]['support']]
                self.level['resistance'] = [[ls[0],ls[1],datetime.datetime.strptime(ls[2],'%Y-%m-%d %H:%M:%S'),ls[3]] for ls in self.indicator_df.iloc[-1]['resistance']]
            except:
                print("no indicator data for "+sec_name)
        if ~(isinstance(self.latest_db_date, datetime.datetime)):
            self.latest_db_date = datetime.datetime(2000, 1, 1)
    # N: This looks where the fractal points beeing added    
    def add_level(self,support=True):
        # to get the size of the wick and set a flag for the level whether its mergeable
        mergeable_flag=True
        if support:
            if self.ind_dict['wick_bear_dev'][-2]>=3:
                mergeable_flag=False
        else:
            if self.ind_dict['wick_bear_dev'][-2]>=3:
                mergeable_flag=False

        # if ~mergeable_flag:
        #     print(bt.num2date(self.data.datetime[-2]))

        side='Bull' if(self.data.close[-2]>self.data.open[-2]) else 'Bear'
        if(support and side=='Bull'):
            return [self.data.low[-2],self.data.open[-2],bt.num2date(self.data.datetime[-2]),True,mergeable_flag]
        elif(support and side=='Bear'): 
            return [self.data.low[-2],self.data.close[-2],bt.num2date(self.data.datetime[-2]),True,mergeable_flag]
        elif(~support and side=='Bull'):
            return [self.data.high[-2],self.data.close[-2],bt.num2date(self.data.datetime[-2]),True,mergeable_flag]
        elif(~support and side=='Bear'):
            return [self.data.high[-2],self.data.open[-2],bt.num2date(self.data.datetime[-2]),True,mergeable_flag]

    
    def next(self):
        # if self.params.use_db and not self.indicator_df.empty:

        if self.latest_db_date>bt.num2date(self.data.datetime[0]):
            self.l.level[0]=self.indicator_df.loc[bt.num2date(self.data.datetime[0])]['level']

        else:
            last_five_highs = self.data.high.get(size=5)
            last_five_lows = self.data.low.get(size=5)
            
            if(len(last_five_highs)==5 and len(last_five_lows)==5):
                # A bearish turning point occurs when there is a pattern with the
                # highest high in the middle and two lower lows on each side. [Ref 1]
                max_val = max(last_five_highs)
                max_idx = last_five_highs.index(max_val)       
                if max_idx == 2:
                    self.level['resistance'].append(self.add_level(support=False))
                    self.level['resistance']=merging_levels(level=self.level['resistance'],support=False)     

                # A bullish turning point occurs when there is a pattern with the
                # lowest low in the middle and two higher lowers on each side. [Ref 1]
                min_val = min(last_five_lows)
                min_idx = last_five_lows.index(min_val)
                if min_idx == 2:           
                    self.level['support'].append(self.add_level(support=True))
                    self.level['support']=merging_levels(level=self.level['support'])

                #N: If a support is broken then it would turn into a resistance. 
                new_res=[i for i in self.level['support'] if ((self.data.close[0]<i[0]) & (i[3]))]   
                new_supp=[i for i in self.level['resistance'] if ((self.data.close[0]>i[0]) & (i[3]))]

                # Broken Support turns into Resistance and vice versa 
                if(new_res):
                    for i in new_res:
                        # print(i)
                        self.level['resistance'].append([i[1],i[0],i[2],False,i[4]]) # reversing the levels (support to resistance) # The False is to indicate its not a new level. 
                        self.level['resistance']=merging_levels(level=self.level['resistance'],support=False)

                if(new_supp):
                    for i in new_supp:
                        self.level['support'].append([i[1],i[0],i[2],False,i[4]]) # reversing the levels (resistance to support)
                        self.level['support']=merging_levels(level=self.level['support'])


            in_resistance=list(map((lambda x: x if (x[0] >= self.data.close[0]) and (x[1] <= self.data.close[0]) else None),self.level['resistance']))
            in_resistance=list(filter(None.__ne__, in_resistance))
            
            in_support = list(map((lambda x: x if (x[0] <= self.data.close[0]) and (x[1] >= self.data.close[0]) else None),self.level['support']))
            in_support=list(filter(None.__ne__, in_support))
            
            # I think this if else condition is totally uneccessary. Because what happens if there are 2 ranges that close is in
            # I am not sure what this is doing, checking if the close is in more than 2 ranges
            # Keeping it for the time being since I dont think this line 'level' would provide any valuable information.
            if self.level['resistance'] and in_resistance:
                if(len(in_resistance)>1):
                    self.in_res_range=merging_levels(level=in_resistance,support=False)[0] 
                else:
                    self.in_res_range=in_resistance[0]
                self.l.level[0]=1 
            
            elif self.level['support'] and in_support:
                if(len(in_support)>1):
                    self.in_sup_range=merging_levels(level=in_support)[0]
                else:
                    self.in_sup_range=in_support[0]
                self.l.level[0]=-1

            else:
                self.l.level[0]=0
                self.in_res_range=0
                self.in_sup_range=0

            # removing the broken levels
            self.level['resistance']=[i for i in self.level['resistance'] if self.data.close[0]<i[0]]        
            self.level['support']=[i for i in self.level['support'] if self.data.close[0]>i[0]]

            # sorting to bring the nearest first
            self.level['resistance'].sort(key = lambda x: x[0])  
            self.level['support'].sort(key = lambda x: x[0],reverse=True) 

            
            # if self.level['support']: # for support and resistance plotting
            #     self.l.s_out[0]=self.level['support'][0][0] # Alterantive #max([i[0] for i in self.level['support']])
            #     self.l.s_in[0]=self.level['support'][0][1] #max([i[1] for i in self.level['support']])
            # if self.level['resistance']:
            #     self.l.r_out[0]=self.level['resistance'][0][0] #min([i[0] for i in self.level['resistance']])
            #     self.l.r_in[0]=self.level['resistance'][0][1] #min([i[1] for i in self.level['resistance']])

            self.write2db()
        self.write2db_test()


    def write2db_test(self):
        level_db_test={}
        level_db_test['date_price']=bt.num2date(self.data.datetime[0])
        level_db_test['level']=self.l.level[0]
        self.test_list.append(level_db_test)

    def write2db(self):
        level_2_db={}

        # # not the neatest trick at all, done only so that I can get the agregrated W and M price and now the rest, so duplicates of price by number of securities, definitely not elegant
        # level_2_db['open']=self.data.open[0]
        # level_2_db['high']=self.data.high[0]
        # level_2_db['low']=self.data.low[0]
        # level_2_db['close']=self.data.close[0]

        level_2_db['level']=self.l.level[0]

        if self.level['support']:
            level_2_db['support']=self.level['support']
            level_2_db['nearest_support_range']=self.level['support'][0][0:2] # taking the nearest support and taking the range
            level_2_db['nearest_support_duration']=(bt.num2date(self.data.datetime[0])-self.level['support'][0][2]).days # this "days" will give wrong numbers for any other timeframe, so it is actually the timeframe we are dealing with.
            level_2_db['nearest_support_atr_range']=abs(self.data.close[0]-np.mean(self.level['support'][0][0:2]))/self.atr[0] #figuring out how many ATR we are away from that level.

        if self.level['resistance']:
            level_2_db['resistance']=self.level['resistance']
            level_2_db['nearest_resistance_range']=self.level['resistance'][0][0:2] # taking the nearest support and taking the range
            level_2_db['nearest_resistance_duration']=(bt.num2date(self.data.datetime[0])-self.level['resistance'][0][2]).days # this "days" will give wrong numbers for any other timeframe, so it is actually the timeframe we are dealing with.
            level_2_db['nearest_resistance_atr_range']=abs(self.data.close[0]-np.mean(self.level['resistance'][0][0:2]))/self.atr[0] #figuring out how many ATR we are away from that level. 
        
        self.indicator_list.append(json.dumps(level_2_db, indent=4, sort_keys=True, default=str)) # dict to json
        self.date_list.append(bt.num2date(self.data.datetime[0]))

