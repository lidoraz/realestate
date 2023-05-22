_sql_dist_part = """
with t0_dist as (
select     (6371 * acos(
        cos(radians(lat)) * cos(radians({lat})) * cos(radians({long}) - radians(long)) +
        sin(radians(lat)) * sin(radians({lat}))
    )) AS distance_in_km, *  from {table_name}
)
"""


sql_time_series_nadlan = f"""
-- HISTORY PRICE CHANGES OVER TIME REAL TRANS
{_sql_dist_part}
SELECT
    DATE_TRUNC('month', trans_date)::date::VARCHAR AS month,
    count(*) as cnt,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN sq_m_net > 0 THEN price_declared / sq_m_net END) AS median_avg_meter_price,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY price_declared) AS median_price--,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN trans_date >= (MAKE_DATE(year_built, 1, 1) + INTERVAL '2 years') and sq_m_net > 0  THEN price_declared / sq_m_net END) AS old_median_avg_meter_price,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN trans_date <= (MAKE_DATE(year_built, 1, 1) + INTERVAL '2 years') and sq_m_net > 0 THEN price_declared / sq_m_net END) AS new_median_avg_meter_price,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN trans_date >= (MAKE_DATE(year_built, 1, 1) + INTERVAL '2 years') THEN price_declared  END) AS old_median_price,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN trans_date <= (MAKE_DATE(year_built, 1, 1) + INTERVAL '2 years') THEN price_declared END) AS new_median_price
FROM t0_dist where 1=1
and deal_part = 1
and distance_in_km < {{dist_km}}
GROUP BY DATE_TRUNC('month', trans_date)
ORDER BY DATE_TRUNC('month', trans_date);"""

sql_time_series_recent = f"""
{_sql_dist_part}

SELECT
    DATE_TRUNC('week', processing_date)::date::varchar AS week,
    count(*) as cnt,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY CASE WHEN square_meters > 0 THEN price / square_meters END) AS avg_price,
    percentile_cont(0.5) WITHIN GROUP (ORDER by price) AS price--,
  --  count(*) FILTER (WHERE asset_status in ('במצב שמור', 'דרוש שיפוץ', 'משופץ')) AS old_cnt,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER by case when asset_status in ('במצב שמור', 'דרוש שיפוץ', 'משופץ') then price end) AS old_prices,
  --  count(*) FILTER (WHERE asset_status in ('חדש (גרו בנכס)', 'חדש מקבלן (לא גרו בנכס)')) AS new_cnt,
  --  percentile_cont(0.5) WITHIN GROUP (ORDER by case when asset_status in ('חדש (גרו בנכס)', 'חדש מקבלן (לא גרו בנכס)') then price end) AS new_prices
FROM t0_dist where 1=1
and distance_in_km < {{dist_km}}
and active = False
and processing_date >= '2023-03-01' -- Only from March data is consist
GROUP BY 1
ORDER BY 1;"""


sql_similar_deals = f"""
{_sql_dist_part}
select * from t0_dist where 1=1
and deal_part = 1
and trans_date  > (Now() - interval '{{n_months}} Month')::date
and round(n_rooms) = round({{n_rooms}}) 
and distance_in_km < 1.5
"""
