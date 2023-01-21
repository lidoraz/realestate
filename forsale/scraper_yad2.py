import requests
import schedule
from tqdm import tqdm
import time
import pandas as pd
from datetime import datetime
import sqlite3

url_forsale_apartments_houses = "https://gw.yad2.co.il/feed-search-legacy/realestate/forsale?propertyGroup=apartments,houses&page={}&forceLdLoad=true"
TRIES = 5


def _get_retry_json(p):
    res = None
    for _ in range(TRIES):
        try:
            res = requests.get(url_forsale_apartments_houses.format(p))
            if res.status_code == 200:
                break
            else:
                print("Status code err")
        except Exception as e:
            print("Caught an exception in get retry")
    if res:
        return res.json()
    return res


def scraper_yad2():
    df = pd.DataFrame()
    res = _get_retry_json(1)
    last_page = res['data']['pagination']['last_page']
    for p in tqdm(range(2, last_page + 1)):
        forsale_data = _get_retry_json(p)
        df_forsale = pd.DataFrame.from_dict(forsale_data['data']['feed']['feed_items'])
        df_forsale = df_forsale[df_forsale['type'] == 'ad']
        df = pd.concat([df, df_forsale], axis=0)
    df = df.reset_index(drop=True)
    return df


def save_current(df):
    # images have double columns, prob for legacy
    redundant_cols = ['images', 'default_layout', 'can_change_layout', 'ad_type', 'IsVisibleForReco',
                      'can_hide', 'external', 'is_hidden', 'is_liked', 'is_trade_in_button',
                      'like_count', 'line_1_text_color', 'line_2_text_color', 'remove_on_unlike', 'type',
                      'uid', 'priority', 'background_type', 'title', 'row_5', 'deal_info', 'currency_text',
                      'mp4_video_url', 'broker_avatar']
    df.drop(columns=redundant_cols)
    df.to_csv('resources/yad2_today.csv')


def check_exists():
    con = sqlite3.connect('resources/yad2.db')
    _check_exists(datetime.today().strftime('%Y%m%d'), con)


def _check_exists(today_str, con):
    cnt_today = pd.read_sql(f"SELECT count(*) from history where processing_date = '{today_str}'", con).squeeze()
    if cnt_today > 0:
        raise ValueError(f"Data from {today_str} already saved in db, total {cnt_today} rows")


def log_history(df):
    con = sqlite3.connect('resources/yad2.db')
    minimum_cols = ['id', 'price', 'date', 'date_added']
    df_price = df[minimum_cols].copy()
    process_price = lambda x: None if x == 'לא צוין מחיר' else x.replace(',', '').replace(' ₪', '')
    df_price['price'] = df_price[minimum_cols]['price'].apply(process_price)
    today_str = datetime.today().strftime('%Y%m%d')
    df_price['processing_date'] = today_str
    _check_exists(today_str, con)
    df_price.to_sql(name='history', con=con, if_exists='append', index=False)


def daily_logic():
    try:
        df = scraper_yad2()
        save_current(df)
        log_history(df)
    except Exception as e:
        print("Caught an exception at scraper yad2!")


if __name__ == '__main__':
    # daily_logic()
    check_exists()
    schedule.every().day.at("00:00").do(daily_logic)

    while True:
        schedule.run_pending()
        time.sleep(1)
