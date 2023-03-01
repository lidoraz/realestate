import os

import numpy as np
import requests
import schedule
from tqdm import tqdm
import time
import pandas as pd
from datetime import datetime
import sqlite3

import sqlalchemy

history_dtype = {
    "price": sqlalchemy.Integer,
    "processing_date": sqlalchemy.Date
}

url_forsale_apartments_houses = "https://gw.yad2.co.il/feed-search-legacy/realestate/forsale?propertyGroup=apartments,houses&page={}&forceLdLoad=true"
url_rent_apartments_houses = "https://gw.yad2.co.il/feed-search-legacy/realestate/rent?propertyGroup=apartments,houses&page={}&forceLdLoad=true"
TRIES = 5
N_THREADS_ITEM_ADD = 10

forsale_today_cols = ['line_1', 'line_2', 'line_3', 'row_1', 'row_2', 'row_3', 'row_4',
                      'search_text', 'title_1', 'title_2', 'images_count', 'img_url',
                      'images_urls', 'video_url', 'primaryarea', 'primaryareaid',
                      'areaid_text', 'secondaryarea', 'area_id', 'city', 'city_code',
                      'street', 'coordinates', 'geohash', 'ad_highlight_type',
                      'background_color', 'highlight_text', 'order_type_id', 'ad_number',
                      'cat_id', 'customer_id', 'feed_source', 'id', 'link_token', 'merchant',
                      'contact_name', 'merchant_name', 'record_id', 'subcat_id', 'currency',
                      'price', 'date', 'date_added', 'updated_at', 'promotional_ad',
                      'address_more', 'hood_id', 'office_about', 'office_logo_url',
                      'square_meters', 'hometypeid_text', 'neighborhood',
                      'assetclassificationid_text', 'rooms_text', 'aboveprice', 'is_platinum',
                      'is_mobile_platinum', 'processing_date']
# Can use this to classify::
# 'PrimaryArea': 'hamerkaz_area'
# 'AreaID_text': 'אזור רמת גן וגבעתיים'
rent_today_cols = ['line_1', 'line_2', 'line_3', 'row_1', 'row_2', 'row_3', 'row_4',
                   'search_text', 'title_1', 'title_2', 'images_count', 'img_url',
                   'images_urls', 'video_url', 'primaryarea', 'primaryareaid',
                   'areaid_text', 'secondaryarea', 'area_id', 'city', 'city_code',
                   'street', 'coordinates', 'geohash', 'ad_highlight_type',
                   'background_color', 'highlight_text', 'order_type_id', 'ad_number',
                   'cat_id', 'customer_id', 'feed_source', 'id', 'link_token', 'merchant',
                   'contact_name', 'merchant_name', 'record_id', 'subcat_id', 'currency',
                   'price', 'date', 'date_added', 'updated_at',
                   'address_more', 'hood_id', 'office_about', 'office_logo_url',
                   'square_meters', 'hometypeid_text', 'neighborhood',
                   'assetclassificationid_text', 'rooms_text', 'aboveprice', 'processing_date']

q_history_last_price = """SELECT id, price as last_price from (select id, price, processing_date, ROW_NUMBER() over (partition by id order by processing_date desc)
 as rn from {}) a where rn=1"""


def remove_dup(table, partitions, con):
    partitions = [partitions] if not isinstance(partitions, list) else partitions
    partitions_str = ', '.join(partitions)
    q_today_remove_duplicates = f"""
    DELETE FROM {table}
    WHERE ctid IN(
        SELECT ctid
        FROM (SELECT ctid,
        ROW_NUMBER() OVER (PARTITION BY {partitions_str}) AS rn
        FROM {table}) t
        WHERE rn > 1)
    """
    con.execute(q_today_remove_duplicates)


def _process_price(x):
    if x == 'לא צוין מחיר':
        return None
    else:
        return x.replace(',', '').replace(' ₪', '').replace(' $', '')


def _get_parse_item_add_info(item_id):
    yad2_url_item = "https://gw.yad2.co.il/feed-search-legacy/item?token={}"
    try:
        d = requests.get(yad2_url_item.format(item_id)).json()['data']
        is_bad = d.get('error_message') is not None
        if is_bad:
            return None
        items_v2 = {x['key']: x['value'] for x in d['additional_info_items_v2']}
        add_info = dict(id=item_id,
                        parking=0 if d['parking'] == "ללא" else int(d['parking']),
                        balconies=True if d['balconies'] else False,
                        number_of_floors=d['TotalFloor_text'],
                        renovated=items_v2.get('renovated'),
                        asset_exclusive_declaration=items_v2.get('asset_exclusive_declaration'),
                        air_conditioner=items_v2.get('air_conditioner'),
                        bars=items_v2.get('bars'),
                        elevator=items_v2.get('elevator'),
                        boiler=items_v2.get('boiler'),
                        accessibility=items_v2.get('accessibility'),
                        shelter=items_v2.get('shelter'),
                        warhouse=items_v2.get('warhouse'),
                        tadiran_c=items_v2.get('tadiran_c'),
                        furniture=items_v2.get('furniture'),
                        flexible_enter_date=items_v2.get('flexible_enter_date'),
                        kosher_kitchen=items_v2.get('kosher_kitchen'),
                        housing_unit=items_v2.get('housing_unit'),
                        info_text=d['info_text'],
                        image_urls=d['images_urls']
                        )
        return add_info
    except Exception as e:
        print(f"Failed to fetch for {item_id}")
    return None


class ScraperYad2:
    def __init__(self, url, use_cols, today_table, history_table, log_table, item_table):
        self.url = url
        self.use_cols = use_cols
        self.history_table = history_table
        self.today_table = today_table
        self.log_table = log_table
        self.item_table = item_table

    def _get_retry_json(self, p):
        res = None
        for _ in range(TRIES):
            try:
                res = requests.get(self.url.format(p))
                if res.status_code == 200:
                    break
                else:
                    print(f"Status code err, retry {_}/{TRIES}")
                    print(res)
                    time.sleep(10)
            except Exception as e:
                print(f"Caught an exception in get retry {_}/{TRIES}")
                time.sleep(10)
        if res:
            return res.json()
        return res

    def insert_today_temp(self, df, con):
        for col, dtype in df.dtypes.items():
            if dtype == 'object':
                df[col] = df[col].astype(str)
        df.to_sql(name=f'{self.today_table}_temp', con=con, if_exists='append', index=False)

    def track_active(self, con):
        print("Updating log table")
        if not sqlalchemy.inspect(con).has_table(self.log_table):
            print("created table")
            df = pd.read_sql(f"Select * from {self.today_table} limit 1", con)
            df['active'] = True
            df.to_sql(self.log_table, con, index=False)
            con.execute(f"ALTER TABLE {self.log_table} ADD PRIMARY KEY (id);")

        today_ids = pd.read_sql(f"Select distinct id from {self.today_table}", con)['id'].to_list()
        today_ids_s = set(today_ids)
        # case has rows, set active, not active
        logged_ids = pd.read_sql(f"Select id from {self.log_table}", con)['id'].to_list()
        logged_ids_s = set(logged_ids)

        ids_in_both = today_ids_s.intersection(logged_ids_s)
        ids_only_in_today = today_ids_s - logged_ids_s

        print('ids_in_both', len(ids_in_both))
        if len(ids_in_both):
            ids_active_str = [f"'{i}'" for i in ids_in_both]
            res = con.execute(f"DELETE FROM {self.log_table} where id in ({','.join(ids_active_str)})")
            print('DELETED - ', res)

        ids_combined = ids_only_in_today.union(ids_in_both)
        ids_str = [f"'{i}'" for i in ids_combined]
        con.execute(
            f"INSERT INTO {self.log_table} (SELECT *, true FROM {self.today_table} WHERE id in ({','.join(ids_str)}))")
        # Set old ones to not-active
        inactive_ids = logged_ids_s - today_ids_s
        if len(inactive_ids):
            ids_not_active_str = [f"'{id}'" for id in inactive_ids]
            con.execute(f"UPDATE {self.log_table} SET active=false WHERE id in ({','.join(ids_not_active_str)})")
        print("Finished Updating log table!")

    def update_today(self, con):
        con.execute(f"DROP table if exists {self.today_table}")
        # - -----
        # con.execute(f"CREATE TABLE  {self.today_table} AS SELECT * FROM {self.today_table}_temp WHERE 0")
        # con.execute(f"INSERT INTO {self.today_table} SELECT * FROM {self.today_table}_temp")
        # - -----#- -----
        con.execute(f"CREATE TABLE {self.today_table} AS TABLE {self.today_table}_temp")
        con.execute(f"DROP table {self.today_table}_temp")
        remove_dup(self.today_table, 'id', con)
        remove_dup(self.history_table, ['id', 'processing_date'], con)

    def _preprocess(self, df, today_str):
        df = df[df['type'] == 'ad'].copy()
        df['processing_date'] = today_str
        # TODO: Process rooms, חדר אחד , too, info text, cordinates, etc.. according to requirement, but not critical.
        df['price'] = df['price'].apply(_process_price).astype(float)
        df.columns = [c.lower() for c in df.columns]
        df = df[self.use_cols]
        return df

    def create_tables(self, con):
        con.execute(f"DROP table if exists {self.today_table}_temp")
        con.execute(
            f"CREATE TABLE IF NOT EXISTS {self.history_table}(id VARCHAR(255) not null, price float, date TIMESTAMP, date_added TIMESTAMP not null, processing_date DATE not null)")

    def insert_to_items(self, con):
        # item_table = "yad2_forsale_items_add"
        ids = pd.read_sql(f"SELECT id from {self.today_table}", con)['id'].to_list()
        today = datetime.today().date()
        if not sqlalchemy.inspect(con).has_table(self.item_table):
            entry = pd.Series(_get_parse_item_add_info(ids[0])).to_frame().T
            entry['processing_date'] = today
            entry.to_sql(self.item_table, con, index=False)
            con.execute(f"ALTER TABLE {self.item_table} ADD PRIMARY KEY (id);")

        ids_in_items = pd.read_sql(f"SELECT id from {self.item_table}", con)['id'].to_list()
        ids_to_insert = list(set(ids) - set(ids_in_items))
        print(f"Preparing to insert: {len(ids_to_insert)} items")
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(N_THREADS_ITEM_ADD) as executor:
            results = list(tqdm(executor.map(_get_parse_item_add_info, ids_to_insert), total=len(ids_to_insert)))
        results = [i for i in results if i is not None]
        df_items = pd.DataFrame(results)
        df_items['processing_date'] = today
        df_items.to_sql(self.item_table, con, if_exists='append', index=False)
        print(f"insert_to_items: Inserted to {self.item_table} {len(df_items)} items!")

    def scraper_yad2(self, con):
        self.create_tables(con)
        res = self._get_retry_json(1)
        last_page = res['data']['pagination']['last_page']
        today_dt = datetime.today()
        df_today_history = pd.read_sql(q_history_last_price.format(self.history_table), con)
        df = None
        for p in tqdm(range(1, last_page + 1)):
            data = self._get_retry_json(p)
            data = data.get('data')
            if data is None:
                print(f"CAUTION - Could not fetch data for part {p}")
            df = pd.DataFrame.from_dict(data['feed']['feed_items'])
            df = self._preprocess(df, today_dt)
            self.log_history(df, df_today_history, con)
            self.insert_today_temp(df, con)
        if df is not None:
            # update only if there was a change(prob was)
            self.update_today(con)
            self.track_active(con)
            self.insert_to_items(con)

    def _check_exists(self, today_str, con):
        cnt_today = pd.read_sql(f"SELECT count(*) from {self.history_table} where processing_date = '{today_str}'",
                                con).squeeze()
        if cnt_today > 0:
            raise ValueError(f"Data from {today_str} already saved in db, total {cnt_today} rows")

    def log_history(self, df, df_today_history, con):
        # will dump only if a price of an id has changed from its current logged price, to save space and efficiency
        minimum_cols = ['id', 'price', 'date', 'date_added', 'processing_date']
        df = df[minimum_cols].copy()
        merged = df[['id', 'price']].merge(df_today_history, left_on='id', right_on='id', how='left')
        merged['last_price'] = merged['last_price'].astype(float)
        # cond with equal, and equal nan, special case
        equal_cond = (merged['price'] == merged['last_price'])
        equal_nan_cond = (merged['price'].isna() & merged['last_price'].isna())
        ids_not_changed = merged[equal_cond | equal_nan_cond]['id'].to_list()
        df = df[~df['id'].isin(ids_not_changed)]
        df.to_sql(name=self.history_table, con=con, if_exists='append', index=False, dtype=history_dtype)


def _get_local_engine():
    eng = sqlalchemy.create_engine(f'sqlite:///{os.getcwd()}/yad2.db')
    return eng


def get_scraper_yad2_forsale():
    scraper = ScraperYad2(url_forsale_apartments_houses, forsale_today_cols,
                          "yad2_forsale_today",
                          "yad2_forsale_history",
                          'yad2_forsale_log',
                          "yad2_forsale_items_add")
    return scraper


def get_scraper_yad2_rent():
    scraper = ScraperYad2(url_rent_apartments_houses, rent_today_cols,
                          "yad2_rent_today",
                          "yad2_rent_history",
                          'yad2_rent_log',
                          "yad2_rent_items_add")
    return scraper


def test_daily_logic_forsale():
    try:
        with _get_local_engine().connect() as con:
            scraper = get_scraper_yad2_forsale()
            scraper.scraper_yad2(con)
        print(f"FINIHSED! - daily_logic_forsale")
    except Exception as e:
        print("Caught an exception at scraper daily_logic_forsale yad2!", e)


def test_daily_logic_rent():
    try:
        with _get_local_engine().connect() as con:
            scraper = get_scraper_yad2_rent()
            scraper.scraper_yad2(con)
        print(f"FINIHSED! - daily_logic_rent")
    except Exception as e:
        print("Caught an exception at scraper daily_logic_rent yad2!", e)


if __name__ == '__main__':
    test_daily_logic_rent()
