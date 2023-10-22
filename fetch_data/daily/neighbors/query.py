q_prices_city_neighborhood = """
select 
 city,
 neighborhood,
 --DATE_TRUNC('MONTH', processing_date)::date::VARCHAR AS MONTH,
 --(extract(day from now() - processing_date) / (30 * 3))::int as relative_quarter,
 min(processing_date) as start_date,
 count(*) as cnt,
 --percentile_cont(0.25) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_25,
 percentile_cont(0.50) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_50,
 --percentile_cont(0.75) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_75,
 --percentile_cont(0.25) WITHIN GROUP (ORDER by price)::int AS price_25,
 percentile_cont(0.5) WITHIN GROUP (ORDER by price)::int AS price_50,
 --percentile_cont(0.75) WITHIN GROUP (ORDER by price)::int AS price_75,
 avg(price)::int as avg_price--,
 --array_agg(lat) as list_lat,
 --array_agg(long) as list_long

 from {table_name} where active = false -- yad2_forsale_log
 and processing_date >= '2023-03-01' -- Only from March data is consist
group by 1, 2, (extract(day from now() - processing_date) / ({calc_every_x_days}))::int
having count(*) >= {min_cnt}
order by 1,2, start_date
"""

q_prices_city = """
select 
 city,
 --DATE_TRUNC('MONTH', processing_date)::date::VARCHAR AS MONTH,
 --(extract(day from now() - processing_date) / (30 * 3))::int as relative_quarter,
 min(processing_date) as start_date,
 count(*) as cnt,
 --percentile_cont(0.25) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_25,
 percentile_cont(0.50) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_50,
 --percentile_cont(0.75) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END)::int AS price_meter_75,
 --percentile_cont(0.25) WITHIN GROUP (ORDER by price)::int AS price_25,
 percentile_cont(0.5) WITHIN GROUP (ORDER by price)::int AS price_50,
 --percentile_cont(0.75) WITHIN GROUP (ORDER by price)::int AS price_75,
 avg(price)::int as avg_price--,
 --array_agg(lat) as list_lat,
 --array_agg(long) as list_long

 from {table_name} where active = false -- yad2_forsale_log
 and processing_date >= '2023-03-01' -- Only from March data is consist
group by city, (extract(day from now() - processing_date) / ({calc_every_x_days}))::int
having count(*) >= {min_cnt}
order by city, start_date
"""

q_polygons_city_neighborhood = """
select 
 city,
 neighborhood,
 array_agg(lat) as list_lat,
 array_agg(long) as list_long
 from {table_name}
 where lat is not null and long is not null
 and processing_date > '2023-04-01'
 group by 1, 2
 having count(*) > 25
"""  # .format(table_name=table_name)
# month, quarter
q_polygons_city = """
select 
 city,
 array_agg(lat) as list_lat,
 array_agg(long) as list_long
 from {table_name}
 where lat is not null and long is not null
 and processing_date > '2023-04-01'
 group by city
 having count(*) > 100
 """