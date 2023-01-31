import numpy as np
import requests
import schedule
from tqdm import tqdm
import time
import pandas as pd
from datetime import datetime
import sqlite3

url_forsale_apartments_houses = "https://gw.yad2.co.il/feed-search-legacy/realestate/forsale?propertyGroup=apartments,houses&page={}&forceLdLoad=true"
TRIES = 5
redundant_cols = ['images', 'default_layout', 'can_change_layout', 'ad_type', 'IsVisibleForReco',
                  'can_hide', 'external', 'is_hidden', 'is_liked', 'is_trade_in_button',
                  'like_count', 'line_1_text_color', 'line_2_text_color', 'remove_on_unlike', 'type',
                  'uid', 'priority', 'background_type', 'title', 'row_5', 'deal_info', 'currency_text',
                  'mp4_video_url', 'broker_avatar']


def _get_retry_json(p):
    res = None
    for _ in range(TRIES):
        try:
            res = requests.get(url_forsale_apartments_houses.format(p))
            if res.status_code == 200:
                break
            else:
                print(f"Status code err, retry {_}/{TRIES}")
        except Exception as e:
            print(f"Caught an exception in get retry {_}/{TRIES}")
    if res:
        return res.json()
    return res


def insert_today_temp(df, con):
    for col, dtype in df.dtypes.items():
        if dtype == 'object':
            df[col] = df[col].astype(str)
    df.to_sql(name='yad2_today_temp', con=con, if_exists='append', index=False)


def update_today(df, con):
    con.execute("DROP table if exists yad2_today")
    con.commit()
    df.sample(0).to_sql(name='today', con=con, index=False)
    con.execute("INSERT INTO today SELECT * FROM yad2_today_temp;")
    con.commit()
    con.execute("DROP table if exists yad2_today_temp")
    con.commit()


def _preprocess(df, today_str):
    df = df[df['type'] == 'ad'].copy()
    df['processing_date'] = today_str
    df = df.drop(columns=redundant_cols)
    return df


def scraper_yad2(con):
    con.execute("DROP table if exists yad2_today_temp")
    con.commit()
    res = _get_retry_json(1)
    last_page = res['data']['pagination']['last_page']
    today_str = datetime.today().strftime('%Y%m%d')
    df = None
    for p in tqdm(range(1, last_page + 1)):
        data = _get_retry_json(p)
        df = pd.DataFrame.from_dict(data['data']['feed']['feed_items'])
        df = _preprocess(df, today_str)
        insert_today_temp(df, con)
        log_history(df, con)
    if df is not None:
        update_today(df, con)


def save_current(df):
    # images have double columns, prob for legacy
    df.drop(columns=redundant_cols)
    df.to_csv('resources/yad2_today.csv')


def check_exists():
    con = sqlite3.connect('resources/yad2.db')
    _check_exists(datetime.today().strftime('%Y%m%d'), con)


def _check_exists(today_str, con):
    cnt_today = pd.read_sql(f"SELECT count(*) from yad2_history where processing_date = '{today_str}'", con).squeeze()
    if cnt_today > 0:
        raise ValueError(f"Data from {today_str} already saved in db, total {cnt_today} rows")


def log_history(df, con):
    minimum_cols = ['id', 'price', 'date', 'date_added', 'processing_date']
    df_price = df[minimum_cols].copy()
    process_price = lambda x: None if x == 'לא צוין מחיר' else x.replace(',', '').replace(' ₪', '')
    df_price['price'] = df_price[minimum_cols]['price'].apply(process_price)
    df_price.to_sql(name='yad2_history', con=con, if_exists='append', index=False)


def daily_logic():
    try:
        con = sqlite3.connect('resources/yad2.db')
        scraper_yad2(con)
        print(f"FINIHSED!")
    except Exception as e:
        print("Caught an exception at scraper yad2!", e)


if __name__ == '__main__':
    daily_logic()
    # check_exists()
    schedule.every().day.at("00:00").do(daily_logic)

    while True:
        schedule.run_pending()
        time.sleep(1)
