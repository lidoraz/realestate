from sqlalchemy import Integer, Date, String, Boolean, BigInteger, INTEGER, DateTime, Float

history_dtype = {
    "price": Integer,
    "processing_date": Date
}

url_forsale_apartments_houses = "https://gw.yad2.co.il/feed-search-legacy/realestate/forsale?propertyGroup=apartments,houses&page={}&forceLdLoad=true"
url_rent_apartments_houses = "https://gw.yad2.co.il/feed-search-legacy/realestate/rent?propertyGroup=apartments,houses&page={}&forceLdLoad=true"
TRIES = 5
N_THREADS_ITEM_ADD = 10
cols_renamer_today = {
    "hometypeid_text": "asset_type",
    "id": "id",
    "price": "price",
    "city": "city",
    "rooms_text": "rooms",
    "line_2": "floor",  # Needs conversion from קרקע to 0 and str
    "square_meters": "square_meters",
    "assetclassificationid_text": "asset_status",  # better cond
    "neighborhood": "neighborhood",
    "street": "street",
    "title_1": "street_num",
    # "primaryarea": "primary_area",
    "primaryareaid": "primary_area_id",
    "area_id": "area_id",
    # "city_code": "city_id",
    "merchant": "is_agency",
    "merchant_name": "agency_name",
    "img_url": "img_url",
    "latitude": "lat",  # Added
    "longitude": "long",  # Added
    "date": "date_updated",
    "date_added": "date_added",
    "processing_date": "processing_date"  # Added
}


forsale_today_cols = ['line_1', 'line_2', 'line_3', 'row_1', 'row_2', 'row_3', 'row_4',
                      'search_text', 'title_1', 'title_2', 'images_count', 'img_url',
                      'images_urls', 'video_url', 'primaryarea', 'primaryareaid',
                      'areaid_text', 'secondaryarea', 'area_id', 'city', 'city_code',
                      'street', 'coordinates', 'geohash', 'ad_highlight_type',
                      'background_color', 'highlight_text', 'order_type_id', 'ad_number',
                      'cat_id', 'customer_id', 'feed_source', 'id', 'link_token', 'merchant',
                      'contact_name', 'merchant_name', 'record_id', 'subcat_id', 'currency',
                      'price', 'date', 'date_added', 'date_updated', 'promotional_ad',
                      'address_more', 'hood_id',  # 'office_about', 'office_logo_url',
                      'square_meters', 'hometypeid_text', 'neighborhood',
                      'assetclassificationid_text', 'rooms_text', 'aboveprice', 'is_platinum',
                      'is_mobile_platinum', 'processing_date']
# Can use this to classify::
# 'PrimaryArea': 'hamerkaz_area'
# 'AreaID_text': 'אזור רמת גן וגבעתיים'

to_be_removed_cols = ['merchant_name', 'currency', 'office_about', 'office_logo_url', ]
rent_today_cols = ['line_1', 'line_2', 'line_3', 'row_1', 'row_2', 'row_3', 'row_4',
                   'search_text', 'title_1', 'title_2', 'images_count', 'img_url',
                   'images_urls', 'video_url', 'primaryarea', 'primaryareaid',
                   'areaid_text', 'secondaryarea', 'area_id', 'city', 'city_code',
                   'street', 'coordinates', 'geohash', 'ad_highlight_type',
                   'background_color', 'highlight_text',
                   'order_type_id', 'ad_number',
                   'cat_id', 'customer_id', 'feed_source', 'id', 'link_token', 'merchant',
                   'contact_name', 'merchant_name',
                   'record_id', 'subcat_id', 'currency',
                   'price', 'date', 'date_added', 'date_updated',
                   'address_more', 'hood_id', 'office_about', 'office_logo_url',
                   'square_meters', 'hometypeid_text', 'neighborhood',
                   'assetclassificationid_text', 'rooms_text', 'aboveprice', 'processing_date']

sql_today_dtypes = {'id': String, 'asset_type': String,
                    'price': BigInteger, 'city': String, 'rooms': Float,
                    'square_meters': Float, 'asset_status': String, 'floor': Integer,
                    'neighborhood': String,
                    'street': String, 'street_num': String,
                    # 'primary_area': String,
                    'primary_area_id': Integer, 'area_id': Integer,
                    # 'city_id': Integer,
                    'is_agency': Boolean, 'agency_name': String,
                    'img_url': String,
                    'lat': Float, 'long': Float, 'date_updated': DateTime,
                    'date_added': DateTime, 'processing_date': Date}

assert len(sql_today_dtypes) == len(cols_renamer_today)

sql_price_history_dtypes = {'id': String, 'price': BigInteger, 'date_updated': DateTime, 'date_added': DateTime,
                            'processing_date': Date}

sql_items_dtypes = {'id': String, 'parking': Integer, 'balconies': Boolean, 'number_of_floors': Integer,
                    'renovated': Boolean, 'asset_exclusive_declaration': Boolean, 'air_conditioner': Boolean,
                    'bars': Boolean, 'elevator': Boolean, 'boiler': Boolean, 'accessibility': Boolean,
                    'shelter': Boolean, 'warhouse': Boolean, 'tadiran_c': Boolean, 'furniture': Boolean,
                    'flexible_enter_date': Boolean, 'kosher_kitchen': String, 'housing_unit': String,
                    'square_meters': Integer, 'square_meter_build': Integer, 'garden_area': Integer,
                    'info_text': String, 'image_urls': String, 'processing_date': Date}

q_history_last_price = """SELECT id, price as last_price from (select id, price, processing_date, ROW_NUMBER() over (partition by id order by processing_date desc)
 as rn from {}) a where rn=1"""
