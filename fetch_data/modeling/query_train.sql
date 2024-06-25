with price_history as (select id,
                              (array_agg(price order by processing_date))[1]                as first_price,
                              (array_agg(price order by processing_date desc))[1]           as last_price,
                              (array_agg(processing_date order by processing_date))[1]      as first_processing_date,
                              (array_agg(processing_date order by processing_date desc))[1] as last_processing_date,
                              array_agg(price order by processing_date)                     as prices,
                              min(price)                                                    as min_price,
                              max(price)                                                    as max_price,
                              avg(price)                                                    as avg_price_chg,
                              coalesce(stddev(price), 0)                                    as std_price_chg,
                              count(*)                                                      as n_changes
                       from yad2_{asset_type}_history
                       where price is not null
                       group by id
--having (array_agg(processing_date order by processing_date desc))[1] > now() - interval '7' day
--order by n_changes desc
),
-- filter exact lat long having too many assets (over 50)
bad_loctions as (select city,
                     --MODE() WITHIN GROUP (ORDER BY city) as city, -- same as abitrary
                     lat,
                     long,
                     lat::varchar || long::varchar as latlong,
                     count(*)                      as cnt_same
              from yad2_{asset_type}_today
              where lat is not null and long is not null
              group by city, lat, long
              having count(*) > 50),
-- used when lat / long is missing from the data, it can be inferred from past data
city_street_num_locs as(
select city, street_num, min(lat) as lat, min(long) as long
from (
select city, street_num, lat, long from yad2_forsale_log union
select city, street_num, lat, long from yad2_rent_log
) a group by city, street_num
),
data_train as (
select a.id,
       price,
       active                                                               as is_active,
       a.asset_type,
--prices,
       coalesce(last_price / first_price::float - 1, 0)                     as price_pct,
       last_price - first_price                                             as price_diff,
       avg_price_chg,
       std_price_chg,
       n_changes,
       a.city,
       rooms,
       coalesce(asset_status, 'U')                                          as asset_status,
       floor,
       coalesce(neighborhood, 'U')                                          as neighborhood,
-- street,street_num,primary_area_id,area_id,
       is_agency,
       TRUNC(coalesce(a.lat, d.lat)::numeric, 4) as lat,
       TRUNC(coalesce(a.long, d.long)::numeric, 4) as long,
       parking,
       balconies,
       coalesce(number_of_floors, 0)                                        as number_of_floors,
       coalesce(renovated, false)                                           as renovated,
       coalesce(asset_exclusive_declaration, false)                         as asset_exclusive_declaration,
       coalesce(air_conditioner, false)                                     as air_conditioner,
       coalesce(bars, false)                                                as bars,
       coalesce(elevator, false)                                            as elevator,
       coalesce(boiler, false)                                              as boiler,
       coalesce(accessibility, false)                                       as accessibility,
       coalesce(shelter, false)                                             as shelter,
       coalesce(warhouse, false)                                            as warhouse,
       coalesce(tadiran_c, false)                                           as tadiran_c,
       coalesce(furniture, false)                                           as furniture,
       coalesce(flexible_enter_date, false)                                 as flexible_enter_date,
       coalesce(kosher_kitchen::bool, false)                                as kosher_kitchen,
       coalesce(housing_unit::bool, false)                                  as housing_unit,
       coalesce(case
                    when square_meter_build = 0 or square_meter_build is null
                        then a.square_meters
                    else square_meter_build end, 0)                         as square_meters,
       coalesce(garden_area, 0)                                             as garden_area,
--info_text,
       info_text like '%דמי מפתח%'                                          as is_keycrap,
       info_text like '%התחדשות עירונית%'                                   as is_city_renew,
       info_text like '%תמא%' or info_text like '%תמ״א%'                    as is_tama,
       info_text like '%לפני תמא%' or info_text like '%לפני תמ"א%'
           or info_text like '%לקראת תמא%' or info_text like '%לקראת תמ"א%' as is_tama_before,
       info_text like '%אחרי תמא%' or info_text like '%אחרי תמ"א%'
           or info_text like '%לאחר תמא%' or info_text like '%לאחר תמ"א%'   as is_tama_after,
       info_text like '%זכות לדירה%'                                        as is_zehut,
       coalesce(array_length(string_to_array(image_urls, ','), 1), 0)       as n_images,
       extract(day from a.processing_date - date_updated)                   as days_last_updated,
       extract(day from a.processing_date - date_added)                     as days_in_market,
       (a.processing_date - date '2023-01-01') / 7.0                        as week_num_from_start
--date_updated,date_added,a.processing_date
from yad2_{asset_type}_log a
join yad2_{asset_type}_items_add b
    on a.id=b.id
join price_history c
    on a.id= c.id
join city_street_num_locs d
    on a.city=d.city and a.street_num=d.street_num
WHERE 1=1
and price is not null
and date_added >= now() - interval '1' year -- pick only recent data
and (a.lat::varchar || a.long::varchar not in (select latlong from bad_loctions))
)
select * from data_train where 1=1
and lat is not null
and long is not null
{price_between_sql}

