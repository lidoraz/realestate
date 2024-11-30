sql_time_series_nadlan = """

-- HISTORY PRICE CHANGES OVER TIME REAL TRANS
with t0_dist as(
SELECT
(6371 * acos(
        cos(radians(lat)) * cos(radians({lat})) * cos(radians({long}) - radians(long)) +
        sin(radians(lat)) * sin(radians({lat}))
)) AS distance_in_km,
price_declared,
sq_m_net,
year_built,
deal_part,
n_rooms,
trans_date
from {table_name}
where deal_part = 1
)
SELECT
    DATE_TRUNC('quarter', trans_date)::date::VARCHAR AS month,
    count(*) as cnt,
    count(case when round(n_rooms) = round({rooms}) then 1 end) as cnt_room,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN sq_m_net > 0 THEN price_declared / sq_m_net END)::int AS median_avg_meter_price,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN round(n_rooms) = round({rooms}) AND sq_m_net > 0 THEN price_declared / sq_m_net END)::int AS median_avg_meter_price_room,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN round(n_rooms) = round({rooms}) THEN price_declared END)::int AS median_price_room,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY price_declared)::int AS median_price--,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN trans_date >= (MAKE_DATE(year_built, 1, 1) + INTERVAL '2 years') and sq_m_net > 0  THEN price_declared / sq_m_net END) AS old_median_avg_meter_price,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN trans_date <= (MAKE_DATE(year_built, 1, 1) + INTERVAL '2 years') and sq_m_net > 0 THEN price_declared / sq_m_net END) AS new_median_avg_meter_price,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN trans_date >= (MAKE_DATE(year_built, 1, 1) + INTERVAL '2 years') THEN price_declared  END) AS old_median_price,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN trans_date <= (MAKE_DATE(year_built, 1, 1) + INTERVAL '2 years') THEN price_declared END) AS new_median_price
FROM t0_dist where 1=1
and distance_in_km < {dist_km}
GROUP BY 1
ORDER BY 1;"""

sql_time_series_recent = """
with t0_dist as(
SELECT
(6371 * acos(
        cos(radians(lat)) * cos(radians({lat})) * cos(radians({long}) - radians(long)) +
        sin(radians(lat)) * sin(radians({lat}))
)) AS distance_in_km,
price,
square_meters,
rooms,
date_added,
processing_date
from {table_name}
where active = False
and processing_date >= '2023-03-01' -- Only from March data is consist
and date_added >= '2023-03-01'
)

SELECT
    DATE_TRUNC('month', date_added)::date::varchar AS week,
    count(*) as cnt,
    count(case when round(rooms) = round({rooms}) then 1 end) as cnt_room,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS avg_price,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN round(rooms) = round({rooms}) THEN price END)::int AS price_room,
    percentile_cont(0.5) WITHIN GROUP (ORDER by price)::int AS price--,
  --  count(*) FILTER (WHERE asset_status in ('במצב שמור', 'דרוש שיפוץ', 'משופץ')) AS old_cnt,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER by case when asset_status in ('במצב שמור', 'דרוש שיפוץ', 'משופץ') then price end) AS old_prices,
  --  count(*) FILTER (WHERE asset_status in ('חדש (גרו בנכס)', 'חדש מקבלן (לא גרו בנכס)')) AS new_cnt,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER by case when asset_status in ('חדש (גרו בנכס)', 'חדש מקבלן (לא גרו בנכס)') then price end) AS new_prices
FROM t0_dist where 1=1
and distance_in_km < {dist_km}
GROUP BY 1
ORDER BY 1;"""


sql_similar_deals = """

with t0_dist as (
SELECT
(6371 * acos(
        cos(radians(lat)) * cos(radians({lat})) * cos(radians({long}) - radians(long)) +
        sin(radians(lat)) * sin(radians({lat}))
)) AS distance_in_km,
price_declared,
deal_part,
trans_date,
n_rooms
from {table_name}
where 1=1 
and deal_part = 1
and trans_date  > (Now() - interval '{n_months} Month')::date
and round(n_rooms) = round({rooms}) 
)
select price_declared from t0_dist where distance_in_km < {dist_km}
"""