
-- Delete data
delete from d_data where id>0

-- To get the latest max, min dates for the data in the indicator DB
select * from (select symbol_id, min(date_price), max(date_price) from d_data group by symbol_id) a join symbol s on s.id=a.symbol_id 

-- Min, Max date for price data
select s.ticker, min(date_price), max(date_price), count(date_price) from d_data d join symbol s on s.id=d.symbol_id  group by s.ticker	

-- Select price data for a security
select a.created_date, a.date_price date, a.open_price open, a.high_price high, a.low_price low, a.close_price as close, a.volume 
from d_data a inner join symbol b on a.symbol_id = b.id where b.ticker='EUR_USD' and a.date_price between '6-17-2020' and '6-19-2020' order by date desc

-- select indicator data 
SELECT indicator_id, symbol_id, a. created_date, a. date_price as date
FROM d_data a inner join symbol b on a.symbol_id = b.id 
where b.ticker='EUR_USD' and a.date_price between '1-1-2020' and '6-19-2020' 
and indicator_id=3 order by date desc;

-- add a new column
ALTER TABLE symbol
ADD identifier TEXT NULL;

! python q_pack/q_run/run_BT.py --strat_name=simple_strategy_3 --mode=backtest --tickers=AUD_USD,EUR_JPY,EUR_USD,GBP_JPY,GBP_USD,NZD_USD,USD_CAD,USD_CHF,USD_JPY --timeframe=daily --strat_param=use_level=no,use_db=yes


!python q_pack/q_run/run_BT.py --fromdate='2016-1-1' --timeframe='w' --load_symbol='True' --strat_param "use_level=yes,use_db=yes,ml_serving=no"