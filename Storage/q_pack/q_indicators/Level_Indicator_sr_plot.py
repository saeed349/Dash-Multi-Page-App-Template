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


import backtrader as bt
import itertools

def frange(lower,upper,value):
    if (lower>upper):
        lower,upper=upper,lower
    
    if(value>=lower and value<=upper):
        return True
    else:
        return False

# N: I have to investigate into the merging of level happens
def merging_levels(level,support=True):
    before_length=0
    after_length=1
    while(before_length!=after_length):
        comb_list=list(itertools.combinations(level,2))
        before_length=len(level)
        ind = 0 if support else 1
        for each in comb_list:
            # the 2 if's are for checking if support1 falls in range of support2 or vice versa
            if(frange(each[0][0],each[0][1],value=each[1][ind])): # checks if the value falls in the range of other two
                merged_level=[min(each[0][0],each[1][0]),max(each[0][1],each[1][1]),min(each[0][2],each[1][2])] if support else\
                         [max(each[0][0],each[1][0]),min(each[0][1],each[1][1]),min(each[0][2],each[1][2])]                
                level.append(merged_level) # add the new support 
                level.remove(each[0]) # delete the older support
                level.remove(each[1])
                after_length=len(level) # updating the change in length
                break # now it will go back to the for loop and there will be a change in length
            elif(frange(each[1][0],each[1][1],value=each[0][ind])):
                merged_level=[min(each[0][0],each[1][0]),max(each[0][1],each[1][1]),min(each[0][2],each[1][2])] if support else \
                         [max(each[0][0],each[1][0]),min(each[0][1],each[1][1]),min(each[0][2],each[1][2])]
                level.append(merged_level)
                level.remove(each[0])
                level.remove(each[1])
                after_length=len(level)
                break
            else:
                after_length=len(level) 
                # now the length would be same, but its not breaking yet, so we'll again go over all the combinations 
#         print(before_length,after_length)
    return level

class Level_Indicator(bt.Indicator):
#     lines = ('fractal_bearish', 'fractal_bullish','Level')
    # lines = ('Level',)
    lines = ('Level','s_out','r_out','s_in','r_in')

    plotinfo = dict(subplot=False)
    
    plotlines = dict(s_out=dict(color='green'),
                        r_out=dict(color='red'),
                        s_in=dict(color='green'),
                        r_in=dict(color='red'))

    params = (('disp',False),)

    
    def __init__(self):

        day_min=7*60
        time_dict={4:1,5:day_min,6:(5*day_min),7:(23*day_min)}
        min_Tperiod=time_dict[self.data._timeframe]*self.data._compression
        max_Tperiod=time_dict[self.data._timeframe]*self.data._compression
        min_period=int((max_Tperiod*1)/min_Tperiod)
        print("Min period=",min_period)
        self.addminperiod(min_period+1)
        
        self.level = {'support':[],
                     'resistance':[],
                     'new_support':[],
                     'new_resistance':[]}

        self.in_res_range=0
        self.in_sup_range=0

        # self.l.s=self.data-.01
        # self.l.r=self.data+.01
        
    # N: This looks where the fractal points beeing added    
    def add_level(self,support=True):
        side='Bull' if(self.data.close[-2]>self.data.open[-2]) else 'Bear'
        if(support and side=='Bull'):
            return [self.data.low[-2],self.data.open[-2],bt.num2date(self.data.datetime[-2])]
        elif(support and side=='Bear'): 
            return [self.data.low[-2],self.data.close[-2],bt.num2date(self.data.datetime[-2])]
        elif(~support and side=='Bull'):
            return [self.data.high[-2],self.data.close[-2],bt.num2date(self.data.datetime[-2])]
        elif(~support and side=='Bear'):
            return [self.data.high[-2],self.data.open[-2],bt.num2date(self.data.datetime[-2])]

    
    def next(self):
        # A bearish turning point occurs when there is a pattern with the
        # highest high in the middle and two lower highs on each side. [Ref 1]
        
#         print("**** ",self.data.datetime.date(0))
#         print("#### ",self.data.datetime.date(0))
        
        
        last_five_highs = self.data.high.get(size=5)
        last_five_lows = self.data.low.get(size=5)
        
        if(len(last_five_highs)==5 and len(last_five_lows)==5):
            max_val = max(last_five_highs)
            max_idx = last_five_highs.index(max_val)

            if max_idx == 2:
#                 self.lines.fractal_bearish[-2] = max_val
                self.level['resistance'].append(self.add_level(support=False))
                self.level['resistance']=merging_levels(level=self.level['resistance'],support=False)     

            # A bullish turning point occurs when there is a pattern with the
            # lowest low in the middle and two higher lowers on each side. [Ref 1]

            min_val = min(last_five_lows)
            min_idx = last_five_lows.index(min_val)

            if min_idx == 2:
#                 self.l.fractal_bullish[-2] = min_val            
                self.level['support'].append(self.add_level(support=True))
                self.level['support']=merging_levels(level=self.level['support'])

            #N: If a support is broken then it would turn into a resistance. 
            new_res=[i for i in self.level['support'] if self.data.close[0]<i[0]]   
            new_supp=[i for i in self.level['resistance'] if self.data.close[0]>i[0]]

            if(new_res):
                for i in new_res:
                    self.level['new_resistance'].append([i[1],i[0],i[2]]) # reversing the levels (support to resistance)
                    self.level['new_resistance']=merging_levels(level=self.level['new_resistance'],support=False)

            if(new_supp):
                for i in new_supp:
                    self.level['new_support'].append([i[1],i[0],i[2]]) # reversing the levels (resistance to support)
                    self.level['new_support']=merging_levels(level=self.level['new_support'])


            all_resistance=self.level['resistance']+self.level['new_resistance']
            all_support=self.level['support']+self.level['new_support']
            
            in_resistance=list(map((lambda x: x if (x[0] >= self.data.close[0]) and (x[1] <= self.data.close[0]) else None),all_resistance))
            in_resistance=list(filter(None.__ne__, in_resistance))
            
            in_support = list(map((lambda x: x if (x[0] <= self.data.close[0]) and (x[1] >= self.data.close[0]) else None),all_support))
            in_support=list(filter(None.__ne__, in_support))
            
            if all_resistance and in_resistance:
                if(len(in_resistance)>1):
                    self.in_res_range=merging_levels(level=in_resistance,support=False)[0]
                else:
                    self.in_res_range=in_resistance[0]
                self.l.Level[0]=1
 
            
            elif all_support and in_support:
                if(len(in_support)>1):
                    self.in_sup_range=merging_levels(level=in_support)[0]
                else:
                    self.in_sup_range=in_support[0]
                self.l.Level[0]=-1

            
            else:
                self.l.Level[0]=0
                self.in_res_range=0
                self.in_sup_range=0
                
            self.level['new_resistance']=[i for i in self.level['new_resistance'] if self.data.close[0]<i[0]]        
            self.level['new_support']=[i for i in self.level['new_support'] if self.data.close[0]>i[0]]

            self.level['resistance']=[i for i in self.level['resistance'] if self.data.close[0]<i[0]]        
            self.level['support']=[i for i in self.level['support'] if self.data.close[0]>i[0]]
            
            if all_support:
                self.l.s_out[0]=max([i[0] for i in all_support])
                self.l.s_in[0]=max([i[1] for i in all_support])
            if all_resistance:
                self.l.r_out[0]=min([i[0] for i in all_resistance])
                self.l.r_in[0]=min([i[1] for i in all_resistance])


        if self.params.disp:
            # print("All Resistance",a)
            print(self.data.datetime.date(0))
            print("Resistance=",self.level['resistance'])
            print("New Resistance=",self.level['new_resistance'])
            print("Support=",self.level['support'])
            print("New Support=",self.level['new_support'],"\n")



                