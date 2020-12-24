import backtrader as bt
import datetime
import pandas as pd
import os
import psycopg2


import boto3
from io import StringIO

import q_credentials.db_secmaster_cred as db_secmaster_cred
import q_credentials.db_indicator_cred as db_indicator_cred
import q_tools.write_db as write_db
import q_tools.read_db as read_db

tframes = {4:'m',#bt.TimeFrame.Minutes
            5:'d',
            6:'w',
            7:'m'}#bt.TimeFrame.Months
                
class indicator_analyzer(bt.Analyzer):
    params = (
        ('conn_secmaster', None),
        ('conn_indicator', None),
        ('write_only_updated',True)
    )
    def __init__(self):

        self.trades = []
        self.cumprofit = 0.0
 
        # symbols=[d._name for d in self.datas]
        # sql="""select ticker, instrument, name, currency,created_date from symbol where ticker in ({})""".format(str(symbols)[1:-1])
        # print("SYMBOLS=",symbols)
        # df_symbols=pd.read_sql(sql,con=self.p.conn_indicator)
        # # print(len(df_symbols))
        # if df_symbols.empty:
        #     sql="select ticker, instrument, name, currency,created_date from symbol where ticker in ({})""".format(str(symbols)[1:-1])
        #     df_symbols=pd.read_sql(sql,con=self.p.conn_secmaster)
        #     if ~df_symbols.empty:
        #         write_db.write_db_dataframe(df=df_symbols, conn=self.p.conn_indicator, table='symbol')

    def get_analysis(self):
        return None

    def stop(self):
        ml_list=[]
        data_size=len(self.data)
        num_of_sec=len(self.datas)
        if self.strategy.p.backtest:   
            for i, d in enumerate(self.datas):
                # print("PODA ",d[0])
                num_of_indicators=int(len(self.strategy.getindicators())/len(self.strategy.datas))
                # print(d._name)
                for j in range(num_of_indicators):
                    sec_name=d._name
                    ind = self.strategy.getindicators()[j*num_of_sec+i]
                    ind_name = ind.aliased
                    ind_list = ind.indicator_list
                    ind_date = ind.date_list
                    final_dict=dict(zip(ind_date,ind_list))
                    ind_df=pd.DataFrame(final_dict.items(),columns=['date_price','value']) 
                    time_frame=tframes[d._timeframe]
                    if d._timeframe == 4:
                        time_frame = 'h'+str(int(d._compression/60))
                    # print(d._timeframe,d._compression,time_frame)
                    write_to_ind_db(write_only_updated=self.p.write_only_updated,sec_name=sec_name, ind_name=ind_name,ind_df=ind_df, time_frame=time_frame,conn_indicator=self.p.conn_indicator,conn_secmaster=self.p.conn_secmaster)


def write_to_ind_db(write_only_updated,sec_name, ind_name, ind_df, time_frame, conn_secmaster,conn_indicator,period=0):

    # loading the data into the symbol table if its not alrady there
    sql="""select * from symbol where ticker='{}'""".format(sec_name)
    df_symbols=pd.read_sql(sql,con=conn_indicator)
    if df_symbols.empty:
        sql="select ticker, instrument, name, currency,created_date from symbol where ticker='{}'""".format(sec_name)
        df_symbols=pd.read_sql(sql,con=conn_secmaster)
        if ~df_symbols.empty:
            write_db.write_db_dataframe(df=df_symbols, conn=conn_indicator, table='symbol')

    sql="SELECT id FROM symbol WHERE ticker = '"+sec_name+"'"
    symbol_id=read_db.read_db_single(sql,conn_indicator)
    sql="SELECT id FROM indicator WHERE name = '"+ind_name+"'"
    ind_id=read_db.read_db_single(sql,conn_indicator)   
    if ind_id=="": # write the indicator name into the DB.
        ind_dict={'name':ind_name,'period':period,'created_date':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'last_updated_date':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        ind_id=write_db.write_db_single(conn=conn_indicator, data_dict=ind_dict, table='indicator',return_col="id")
    data_table=time_frame+"_data"
    # print(data_table, ind_id, symbol_id,sec_name)
    if write_only_updated:
        sql="SELECT max(date_price) FROM %s WHERE indicator_id = %s and symbol_id = %s" %(data_table, ind_id, symbol_id)
        print("CUTTING DATA OFF")
        latest_date=read_db.read_db_single(sql,conn_indicator)  
        if isinstance(latest_date, datetime.datetime):
            ind_df=ind_df[ind_df['date_price']>latest_date]
    # print("WRITING THE INDICATOR DATA")
    # ind_df.to_csv('to_write_indicator.csv')
    ind_df['symbol_id'] = symbol_id
    ind_df['indicator_id'] = ind_id
    ind_df['created_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_db.write_db_dataframe(df=ind_df, conn=conn_indicator, table=data_table) 
    # print("done")
    # 

