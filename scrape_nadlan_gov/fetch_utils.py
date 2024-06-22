import uuid
import requests
import pandas as pd
import time

# TODO: ADD TENEACNY TO WAIT EXPO
# !pip install requests==2.24
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


def get_payload(city_id, page_num):
    assert page_num > 0
    payload = {
        "ObjectID": f"{city_id}",  # "5000",
        "CurrentLavel": 2,
        "PageNo": page_num,
        "OrderByFilled": "DEALDATETIME",
        "OrderByDescending": True,
    }
    return payload


def make_request_ordered(payload):
    res = requests.post(url, json=payload, headers=headers, timeout=60)
    if res.status_code == 200:
        data = res.json()
        return data, 200
    return None, res.status_code


def fetch_page_data(city_id, page_num, max_retries=5):
    r_payload = get_payload(city_id, page_num)
    for attempt in range(max_retries):
        try:
            data, status_code = make_request_ordered(r_payload)
            if data is not None:
                df_ = pd.DataFrame.from_records(data['AllResults'])
                return df_
            else:
                print(f"Attempt {attempt + 1} failed for page {page_num}, status code: {status_code}")

        except requests.exceptions.SSLError as e:
            print("SSL Error occurred, exiting loop", e)
            raise e
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for page {page_num} with exception: {e}")
        time.sleep(2)  # Wait for 2 seconds before retrying

    print(f"ERROR: PAGE: {page_num} - All {max_retries} retries failed")
    return pd.DataFrame()
