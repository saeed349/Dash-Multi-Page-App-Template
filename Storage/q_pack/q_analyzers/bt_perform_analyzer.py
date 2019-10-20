####
# Important Note: If there's already an open position in the account during live trading, this will error out because we are recording round trip trades 
####
import backtrader as bt
import datetime

import psycopg2
import q_credentials.db_risk_cred as db_risk_cred

class trade_list(bt.Analyzer):

    def get_analysis(self):

        return self.trades


    def __init__(self):

        self.trades = []
        self.cumprofit = 0.0
        self.conn = psycopg2.connect(host=db_risk_cred.dbHost , database=db_risk_cred.dbName, user=db_risk_cred.dbUser, password=db_risk_cred.dbPWD)

    def notify_trade(self, trade):

        if trade.isclosed:

            brokervalue = self.strategy.broker.getvalue()

            dir = 'short'
            if trade.history[0].event.size > 0: dir = 'long'

            pricein = trade.history[len(trade.history)-1].status.price
            priceout = trade.history[len(trade.history)-1].event.price
            datein = bt.num2date(trade.history[0].status.dt)
            dateout = bt.num2date(trade.history[len(trade.history)-1].status.dt)
            if trade.data._timeframe >= bt.TimeFrame.Days:
                datein = datein.date()
                dateout = dateout.date()

            pcntchange = 100 * priceout / pricein - 100
            pnl = trade.history[len(trade.history)-1].status.pnlcomm
            pnlpcnt = 100 * pnl / brokervalue
            barlen = trade.history[len(trade.history)-1].status.barlen
            pbar = pnl / barlen
            self.cumprofit += pnl

            size = value = 0.0
            for record in trade.history:
                if abs(size) < abs(record.status.size):
                    size = record.status.size
                    value = record.status.value

            highest_in_trade = max(trade.data.high.get(ago=0, size=barlen+1))
            lowest_in_trade = min(trade.data.low.get(ago=0, size=barlen+1))
            hp = 100 * (highest_in_trade - pricein) / pricein
            lp = 100 * (lowest_in_trade - pricein) / pricein
            if dir == 'long':
                mfe = hp
                mae = lp
            if dir == 'short':
                mfe = -lp
                mae = -hp

            analyzer_result={'strategy':self.strategy.alias,'recorded_time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'ref': trade.ref, 'ticker': trade.data._name, 'direction': dir,
                 'datein': datein, 'pricein': pricein, 'dateout': dateout, 'priceout': priceout,
                 'change_percentage': round(pcntchange, 2), 'pnl': pnl, 'pnl_percentage': round(pnlpcnt, 2),
                 'size': size, 'value': value, 'cumpnl': self.cumprofit,
                 'nbars': barlen, 'pnl_per_bar': round(pbar, 2),
                 'mfe_percentage': round(mfe, 2), 'mae_percentage': round(mae, 2)}

            cols=analyzer_result.keys()
            cols_val_list=['%('+i+')s' for i in cols]
            cols_val=", ".join(cols_val_list)
            cols=", ".join(cols)

            cur = self.conn.cursor()
            sql="""INSERT INTO performance ("""+cols+""") VALUES ("""+cols_val+""")"""
            cur.executemany(sql,[analyzer_result]) # this can also support list of dicts
            self.conn.commit()


            self.trades.append(analyzer_result)

def insert_new_vendor(vendor, conn):
    """
    Create a new vendor in data_vendor table.
    args:
        vendor: name of our vendor, type string.
        conn: a Postgres DB connection object
    return:
        None
    """
    todays_date = datetime.datetime.utcnow()
    cur = conn.cursor()
    cur.execute(
                "INSERT INTO performance(name, created_date, last_updated_date) VALUES (%s, %s, %s)",
                (vendor, todays_date, todays_date)
                )
    conn.commit()