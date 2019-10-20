-- This is to get the duplicate rows 
select distinct stock_id from (
	SELECT stock_id, date_price, COUNT(*)
FROM daily_data
GROUP BY stock_id, date_price
HAVING COUNT(*) > 1) as x


-- Removes the duplicate rows
DELETE
FROM
    daily_data a
        USING daily_data b
WHERE
    a.id > b.id
    AND a.stock_id = b.stock_id
	AND a.date_price = b.date_price
	
	