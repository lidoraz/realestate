import requests
import concurrent.futures
import urllib3

from scrape_nadlan_gov.process import process_nadlan_data
from scrape_nadlan_gov.utils import load_json

# Does not work, moving to requests == 2.24
# !pip install requests==2.24
# requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'AES128-SHA'  # 'ALL:@SECLEVEL=2'

import uuid
import pandas as pd
from tqdm import tqdm
from scrape_nadlan_gov.fetch_utils import fetch_page_data

url = "https://www.nadlan.gov.il/Nadlan.REST/Main/GetAssestAndDeals"

headers = {
    "Host": "www.nadlan.gov.il",
    "User-Agent": "Mozilla/5.0 " + str(uuid.uuid4()),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": "application/json;charset=utf-8",
    # "Content-Length": "704",
    "Origin": "https://www.nadlan.gov.il",
    "Connection": "keep-alive",
    "Referer": "https://www.nadlan.gov.il/?",
    "Cookie": "",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"}

cities = load_json('resources/cities_ids.json')


def fetch_by_city(city: str, max_days_back: int, max_pages=10_000):
    df = pd.DataFrame()
    fetch_until = (pd.Timestamp.now() - pd.to_timedelta(max_days_back, unit="D"))
    min_date = None
    city_id = cities.get(city)
    if city_id is None:
        raise ValueError(f"City {city} not found in cities list")
    for i in range(1, max_pages):
        df_ = fetch_page_data(city_id, i)
        df = pd.concat([df, df_], axis=0)
        min_date = pd.to_datetime(df_["DEALDATETIME"]).min()
        print(f"{city=}, {i=}, min_date={str(min_date.date())}, fetch_until={str(fetch_until.date())}")
        if min_date < fetch_until:
            break
    df['city'] = city
    print(f"Fetched {len(df)} rows up to {min_date}")
    return df


def concurrent_fetch_all_cities(max_days_back: int, max_pages=10_000, max_workers=10):
    df = pd.DataFrame()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_city = {executor.submit(fetch_by_city, city, max_days_back, max_pages): city for city in
                          cities}
        # Process results as they complete
        for future in tqdm(concurrent.futures.as_completed(future_to_city), total=len(future_to_city)):
            city = future_to_city[future]
            try:
                df_ = future.result()
                df = pd.concat([df, df_], axis=0)
            except Exception as e:
                print(f"Error fetching data for city {city}: {e}")
    print(f"Fetched {len(df)} rows")
    return df


def test_fetch_by_city():
    df = fetch_by_city('חיפה', 10)
    df = process_nadlan_data(df)

    print(df)
    assert len(df) > 0


def test_fetch_all_cities():
    # 10 => 1620
    # 4 months -> 11860 rows, 35 min
    # 11860 25.598804597059885 ## with 10 threads - only tel aviv is having a lot of data
    import time
    t0 = time.time()
    # 4 months -> 11860 2153 (35 min)
    df = concurrent_fetch_all_cities(max_days_back=30 * 4)
    print(len(df), (time.time() - t0) / 60)
    print()


if __name__ == '__main__':
    # import os
    # os.chdir("..")
    test_fetch_all_cities()
    # test_fetch_by_city_id()
