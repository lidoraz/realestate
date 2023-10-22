#  add scripts here like in sql_scripts to improve stats dashboard, as it is way too slow by loading whole dataframe to memory.
sql_time_series_recent_quantiles_city = """
 select 
 DATE_TRUNC('{time_interval}', processing_date)::date::VARCHAR AS {time_interval},
 city,
 count(*) as cnt,
 percentile_cont(0.25) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_25,
 percentile_cont(0.50) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_50,
 percentile_cont(0.75) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_75,
 percentile_cont(0.25) WITHIN GROUP (ORDER by price)::int AS price_25,
 percentile_cont(0.5) WITHIN GROUP (ORDER by price)::int AS price_50,
 percentile_cont(0.75) WITHIN GROUP (ORDER by price)::int AS price_75,
 avg(price)::int as avg_price
 from {table_name} where active = false -- yad2_forsale_log
 and processing_date >= '2023-03-01' -- Only from March data is consist
 and city in {cities_str}
group by 1, 2 order by 1
"""

sql_time_series_recent_quantiles_all = """
 select 
 DATE_TRUNC('{time_interval}', processing_date)::date::VARCHAR AS {time_interval},
 count(*) as count,
 percentile_cont(0.25) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_25,
 percentile_cont(0.50) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_50,
 percentile_cont(0.75) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_75,
 
 percentile_cont(0.25) WITHIN GROUP (ORDER by price)::int AS price_25,
 percentile_cont(0.5) WITHIN GROUP (ORDER by price)::int AS price_50,
 percentile_cont(0.75) WITHIN GROUP (ORDER by price)::int AS price_75,
 avg(price)::int as avg_price
 from {table_name} where active = false -- yad2_forsale_log
 and processing_date >= '2023-03-01' -- Only from March data is consist
group by 1 order by 1
"""

sql_ratio_time_taken_cities = """
select city,
active_cnt,
not_active_cnt,
active_cnt/not_active_cnt::float as ratio,
median_days_to_not_active,
avg_days_to_not_active  from (
 -- ACTIVE
select city, count(*) as active_cnt
 from {table_name} where active = true group by city having count(*) > {min_samples}) a join 
(
 -- NOT ACTIVE
select city as _city,
count(*) as not_active_cnt,
percentile_cont(0.5) WITHIN GROUP (ORDER by extract(day from (CURRENT_DATE - date_added))::int)::int as median_days_to_not_active,
extract(day from avg(CURRENT_DATE - date_added))::int as avg_days_to_not_active
 from {table_name} where active = false and processing_date >  CURRENT_DATE - interval '{days_back}' day group by city) b
 on a.city = b._city
 order by ratio desc
"""

sql_timeseries_nadlan_prices = """
with t0 as (
select
date_trunc('{time_interval}', trans_date)::date::varchar as {time_interval},
avg(price_declared)::int as mean_price,
percentile_cont(0.5) WITHIN GROUP (ORDER by price_declared) AS median_price,
percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN sq_m_net > 0 THEN price_declared / sq_m_net END)::int AS median_avg_meter_price,
count(*) as cnt,
count(distinct trans_date) as  data_dates
from {table_name}
where now() - trans_date < interval '{year_back} year'
group by 1
)
select *
,(median_price / lag(median_price) over (order by {time_interval}) - 1) * 100 as pct_median
from t0 order by {time_interval}
"""
