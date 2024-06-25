import requests
import pandas as pd
from tqdm import tqdm
import os

from scrape_nadlan_gov.fetch_utils import get_payload, fetch_page_data, url, headers


# Function to make a request and check if it's the last page
def is_last_page(city, page_num, url, headers):
    request_data = get_payload(city, page_num)
    res = requests.post(url, json=request_data, headers=headers)
    if res.status_code == 200:
        data = res.json()
        return data.get('IsLastPage', False)
    else:
        # print(res.text)
        raise Exception(f"Failed to fetch data for page {page_num}")


# Function to perform binary search to find the last page
def find_last_page(city_id, url, headers, max_pages=10_000):
    low, high = 1, max_pages
    last_page = low

    while low <= high:
        print(city_id, low, high)
        mid = (low + high) // 2
        try:
            if is_last_page(city_id, mid, url, headers):
                last_page = mid
                high = mid - 1
            else:
                low = mid + 1
        except Exception as e:
            print(f"Error checking page {mid}: {e}")
            break

    return last_page


import concurrent.futures
import time


def fetch_by_city_id(city_id, max_page_num, max_workers=15):
    # Initialize the final DataFrame
    df = pd.DataFrame()

    # Use ThreadPoolExecutor to run the tasks concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks to the executor
        future_to_page = {executor.submit(fetch_page_data, city_id, page_num): page_num for page_num in
                          range(1, max_page_num)}

        # Process results as they complete
        for future in tqdm(concurrent.futures.as_completed(future_to_page), total=len(future_to_page)):
            page_num = future_to_page[future]
            try:
                df_ = future.result()
                df = pd.concat([df, df_], axis=0)
            except Exception as e:
                print(f"Error fetching data for page {page_num}: {e}")
    print(f"Fetched {len(df)} rows")
    return df


file_path_template = "resources/output/df_{city_id}_{city}.pickle"


def fetch_city(city, city_id, max_page_num=10_000):
    file_path = file_path_template.format(city_id=city_id, city=city)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 500:
        print(f"{city} Already Exists!")

        return pd.read_pickle(file_path)
    print(city)
    max_page_num = find_last_page(city_id, url, headers)
    df = fetch_by_city_id(city_id, max_page_num)
    df['city'] = city
    df.to_pickle(file_path)
    return df


def fetch_all_cities(cities, max_page_num=10_000, max_workers=15):
    for city, city_id in tqdm(cities.items()):
        fetch_city(city, city_id, max_page_num)


if __name__ == '__main__':
    # # this will fetch individual city data and insert it...
    # from scrape_nadlan_gov.insert import insert_new_rows, NadlanGovTrans
    # from scrape_nadlan_gov.process import process_nadlan_data
    from scrape_nadlan_gov.update_cords import process_missing_coordinates
    from ext.env import get_pg_engine
    # city_id = 1247
    # city = "חריש"
    # df = fetch_city(city, city_id)
    # max_days_back = 30 * 12 * 100
    #
    # df = process_nadlan_data(df)
    engine = get_pg_engine()
    # n_rows = df.to_sql(NadlanGovTrans.__tablename__, engine, if_exists='append', index=False)
    #
    # n_rows = insert_new_rows(df, engine, max_days_back)
    # n_fixed_deals = process_missing_coordinates(engine)
    # print("Inserted ", n_rows, " new rows", n_fixed_deals, "fixed deals")

    i =0
    while True:
        i+=1
        n_fixed_deals = process_missing_coordinates(engine)
        print(f"{i=} 10,000 cords...", n_fixed_deals, "fixed deals")
