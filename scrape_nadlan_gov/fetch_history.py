import uuid
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
def find_last_page(city, url, headers, max_pages=10_000):
    low, high = 1, max_pages
    last_page = low

    while low <= high:
        print(city, low, high)
        mid = (low + high) // 2
        try:
            if is_last_page(city, mid, url, headers):
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


def fetch_all_cities(cities, max_page_num=10_000, max_workers=15):
    for city, city_id in tqdm(cities.items()):
        file_path = f"output/df_{city_id}_{city}.pickle"
        if os.path.exists(file_path) and os.path.getsize(file_path) > 500:
            continue
        print(city)
        max_page_num = find_last_page(city_id, url, headers)
        df = fetch_by_city_id(city_id, max_page_num)
        df.to_pickle(f"output/df_{city_id}_{city}.pickle")
