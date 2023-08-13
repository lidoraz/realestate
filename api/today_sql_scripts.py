sql_today_both_rent_sale = """
select
--count(*)
-- a.id as sale_id, b.id as rent_id,
  'https://www.yad2.co.il/item/' || a.id as sale_link,
 'https://www.yad2.co.il/item/' || b.id as rent_link,
 a.city,
 a.price as sale_price, b.price as rent_price,
 round(cast(cast((b.price * 12) as float) / a.price * 100 as numeric), 2)::float as yearly_pct,
 a.date_added::varchar as sale_added,
 b.date_added::varchar as rent_added,
 a.asset_type,
 a.rooms, a.floor,
 a.neighborhood, a.asset_status, a.street_num,
 a.img_url as sale_img,
 b.img_url as rent_img
-- ,a.lat, a.long

from yad2_forsale_today a 
join yad2_rent_today b on
a.lat = b.lat
and a.long = b.long
and a.rooms = b.rooms
and a.floor = b.floor
and a.neighborhood = b.neighborhood
--and a.asset_status = b.asset_status
and a.asset_type = b.asset_type
--and a.square_meters != b.square_meters # so many differences so cant count on this
and a.street_num = b.street_num
and a.street_num  ~ '\d+' -- has a number in streen name
where a.price is not null and b.price is not null
and a.price > 100000
and b.price > 500 and b.price < 100000
and a.img_url is not null
and b.img_url is not null

and  a.date_added > current_date - interval '4 months'
and b.date_added > current_date - interval '4 months'


order by yearly_pct desc
--and a.city = 'חריש' and a.rooms = 4
limit {limit}
"""