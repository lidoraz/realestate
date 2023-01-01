import requests
import selenium
import time
from selenium import webdriver  # , WebDriverWait
from selenium.webdriver.support.ui import Select
import pandas as pd

from DB import DB
from gcloud_test import OCR

from scraper_logic import Scraper
from datetime import datetime, timedelta
def test_case_1():
    from_gush = 7164
    to_gush = 7168  # 7171
    since = '2019-01-01'
    scraper = Scraper()
    df_all = scraper.get_history(from_gush, to_gush, since=since)
    if len(df_all) == 0:
        print('Got a problem...')
    out_str = f"res/test_{from_gush}_{to_gush}_{since.replace('-', '_')}.csv"
    df_all.to_csv(out_str, index=False)
    print(f'Saved to {out_str}')


def test_case_1():
    # https://www.gov.il/apps/mapi/parcel_address/parcel_address.html
    # from_gush = 7164
    # to_gush = 7168 # 7171
    from_gush = 7174
    to_gush = 7174
    value_months = "2"
    scraper = Scraper()
    df_all = scraper.get_months(from_gush, to_gush, value_months)
    if len(df_all) == 0:
        print('Got a problem...')
    out_str = f"res/test_{from_gush}_{to_gush}_{value_months}.csv"
    df_all.to_csv(out_str, index=False)
    print(f'Saved to {out_str}')


def test_case_daily_fetch(date, scraper: Scraper = None):
    # IF FAILED to fetch daily because of err -2, can split the fetch for different rooms, from 1 to 2.5, to 3 to 3.5, from 4 to 4.5, and 5 and more,
    print(f"test_case_daily_fetch - {date}")
    from_gush = 1
    to_gush = 999999
    from datetime import datetime, timedelta
    # days_delta = 14  # should be 1
    # d = (datetime.today() - timedelta(days=days_delta)).strftime("%d/%m/%Y")
    if scraper is None:
        scraper = Scraper()
    df, status_code = scraper.get_daily(from_gush, to_gush, date)
    if status_code == 0:
        db = DB()
        df['insertionDate'] = datetime.today()
        cnt = db.insert_ignore(df)
        print(f"Inserted for date {date} {cnt}/{len(df)} rows to db")
    elif status_code == -1:
        print(f"Could not find deals for {date}")


def get_over_monthly():
    from tqdm import tqdm
    # print("SLEEPING BEFORE")
    # time.sleep(15 * 60)  # TODO: REmove this later
    scraper = Scraper()
    from utils import sleep
    t_tries = 4
    # days_delta = 14  # should be 1

    days_before = 4  # 300
    all_dates = pd.date_range('2022-03-07', datetime.today() - timedelta(days=days_before))
    # all_dates = pd.date_range('2022-03-07', '2022-06-21')

    q_grp_over100 = "select distinct tarIska from trans group by tarIska having count(*) > 100"
    dates_with_data = pd.read_sql(q_grp_over100, DB().con)['tarIska'].apply(
        lambda x: pd.to_datetime(x, format='%Y%m%d')).to_list()
    all_dates = [d for d in all_dates if d not in dates_with_data]

    for d in tqdm(all_dates):
        d = d.strftime("%d/%m/%Y")
        n_try = 0
        # need to split days in case of many
        print(f"Starting to fetch for date: {d}")
        while n_try < t_tries:
            try:
                test_case_daily_fetch(d, scraper)
                print(f"Finished to fetch for date: {d}")
                break
            except Exception as e:
                n_try += 1
                print(f"COULD NOT FETCH DATA FOR DATE: {d} tries: ({n_try},{t_tries})")
                print(e)
                raise e
                sleep(12 * 60)
                scraper.restart_page()
        if n_try == t_tries:
            print(f"COULD NOT FETCH DATA FOR DATE: {d}, GIVE UP AFTER {t_tries} tries!!!!")
            sleep(12 * 60)
        scraper.restart_page()
    scraper.driver.quit()


if __name__ == "__main__":

    date_minus30 = datetime.today() - timedelta(days=30)
    date_minus30 = date_minus30.strftime("%d/%m/%Y")
    test_case_daily_fetch(date_minus30)
    # get_over_monthly()
    # test_case_1()
    print("Hello, World!")
    # test_case_daily_fetch()
