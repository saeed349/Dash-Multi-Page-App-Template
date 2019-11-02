
import pyfolio as pf
import gzip
import os
import pandas as pd
import pytz
# silence warnings
import warnings
warnings.filterwarnings('ignore')


transactions = pd.read_csv(gzip.open("Data/Pyfolio Test/test_txn.csv.gz"),index_col=0, parse_dates=True)
positions = pd.read_csv(gzip.open("Data/Pyfolio Test/test_pos.csv.gz"),index_col=0, parse_dates=True)
returns = pd.read_csv(gzip.open("Data/Pyfolio Test/test_returns.csv.gz"),index_col=0, parse_dates=True)

sect_map = {'COST': 'Consumer Goods', 'INTC':'Technology', 'CERN':'Healthcare', 'GPS':'Technology',
            'MMM': 'Construction', 'DELL': 'Technology', 'AMD':'Technology'}


pf.create_returns_tear_sheet(returns=returns)