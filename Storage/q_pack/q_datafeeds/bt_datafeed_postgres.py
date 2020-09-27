from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
from backtrader.feed import DataBase
from backtrader import date2num
from sqlalchemy import create_engine


class PostgreSQL_Historical(DataBase):
    params = (
        ('conn', None),
        ('ticker', 'EUR_USD'),
        ('fromdate', datetime.datetime.min),
        ('todate', datetime.datetime.max),
        ('name', ''),
        ('db','d')
        )

    def start(self):
        # sql = "select a.date_price date, a.open_price open, a.high_price high, a.low_price low, a.close_price as close, a.volume from " + self.p.db + "_data a inner join symbol b on a.symbol_id = b.id where b.ticker='"+ self.p.ticker + "' and a.date_price between '"+self.p.fromdate.strftime("%Y-%m-%d")+"' and '"+self.p.todate.strftime("%Y-%m-%d")+"' order by date ASC"
        sql ="""select * from 
        (
        select a.date_price date, a.open_price open, a.high_price high, a.low_price low, a.close_price as close, a.volume,
        row_number() over(partition by a.date_price, a.symbol_id order by a.created_date desc) as rn
        from  {}_data a
        inner join symbol b on a.symbol_id = b.id 
        where b.ticker='{}' and a.date_price between '{}' and '{}' 
        ) t
        where t.rn = 1""".format(self.p.db,self.p.ticker,self.p.fromdate.strftime("%Y-%m-%d"),self.p.todate.strftime("%Y-%m-%d"))

        self.result = self.p.conn.execute(sql)


    def _load(self):
        one_row = self.result.fetchone()
        if one_row is None:
            return False
        self.lines.datetime[0] = date2num(one_row[0])
        self.lines.open[0] = float(one_row[1])
        self.lines.high[0] = float(one_row[2])
        self.lines.low[0] = float(one_row[3])
        self.lines.close[0] = float(one_row[4])
        self.lines.volume[0] = int(one_row[5])
        self.lines.openinterest[0] = -1
        return True