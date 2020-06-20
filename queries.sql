
-- Delete data
delete from daily_data where id>0

-- To get the latest max, min dates for the data in the indicator DB
select * from (select symbol_id, min(date_price), max(date_price) from daily_data group by symbol_id) a join symbol s on s.id=a.symbol_id 

-- Min, Max date for price data
select s.ticker, min(date_price), max(date_price), count(date_price) from minute_data d join symbol s on s.id=d.stock_id  group by s.ticker	

-- Select price data for a security
select a.created_date, a.date_price date, a.open_price open, a.high_price high, a.low_price low, a.close_price as close, a.volume 
from minute_data a inner join symbol b on a.stock_id = b.id where b.ticker='EUR_USD' and a.date_price between '6-17-2020' and '6-19-2020' order by date desc

-- select indicator data 
SELECT indicator_id, symbol_id, a. created_date, a. date_price as date
FROM daily_data a inner join symbol b on a.symbol_id = b.id 
where b.ticker='EUR_USD' and a.date_price between '1-1-2020' and '6-19-2020' 
and indicator_id=3 order by date desc;