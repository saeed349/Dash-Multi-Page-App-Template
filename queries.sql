
-- Delete data
delete from daily_data where id>0

-- To get the latest max, min dates for the data in the indicator DB
select * from (select symbol_id, min(date_price), max(date_price) from daily_data group by symbol_id) a join symbol s on s.id=a.symbol_id 

-- Min, Max date for price data
select s.ticker, min(date_price), max(date_price), count(date_price) from minute_data d join symbol s on s.id=d.stock_id  group by s.ticker	