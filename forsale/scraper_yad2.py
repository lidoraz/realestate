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


def _process_price(x):
    if x == 'לא צוין מחיר':
        return None
    else:
        return x.replace(',', '').replace(' ₪', '').replace(' $', '')


class ScraperYad2:
    def __init__(self, url, use_cols, today_table, history_table):
        self.url = url
        self.use_cols = use_cols
        self.history_table = history_table
        self.today_table = today_table

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

    def update_today(self, con):
        con.execute(f"DROP table if exists {self.today_table}")
        con.execute(f"CREATE TABLE {self.today_table} AS TABLE {self.today_table}_temp")
        con.execute(f"DROP table if exists {self.today_table}_temp")

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
            self.update_today(con)

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
        ids_not_changed = merged[merged['price'] == merged['last_price'].astype(float)]['id'].to_list()
        df = df[~df['id'].isin(ids_not_changed)]
        df.to_sql(name=self.history_table, con=con, if_exists='append', index=False, dtype=history_dtype)


def _get_local_engine():
    eng = sqlalchemy.create_engine(f'sqlite:///{os.getcwd()}/yad2.db')
    return eng


def get_scraper_yad2_forsale():
    scraper = ScraperYad2(url_forsale_apartments_houses, forsale_today_cols,
                          "yad2_forsale_today",
                          "yad2_forsale_history")
    return scraper


def get_scraper_yad2_rent():
    scraper = ScraperYad2(url_rent_apartments_houses, rent_today_cols,
                          "yad2_rent_today",
                          "yad2_rent_history")
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
