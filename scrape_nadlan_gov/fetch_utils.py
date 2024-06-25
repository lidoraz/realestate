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
    "Referer": "https://www.nadlan.gov.il/",
    "Cookie": "p_hosting=!28Hz/64OtrA4lR4LfoWcnEfK+F/M7X2T9T9Y+uo1gs4eqlj8+SaX4nno5qCLm+7WcnqTDKSa/HnPIqI=; TS01c75138=0124934a81c86ab815c92886929c00b722adfdec1f383aa7031667d604bd66d98003beeb1bb1568a96cb5fb6c9f46cf9b3f9876d2ccc85ea1f36a39708e0e732523411c4ac; TS0100db2f=0124934a813e6930dd1dfa64c8cbc0e43511b44e3840b5a5b58471d1a5f6a1396410456be27fc23b18522a0c411ed7441968c9d02e48c9522b406675803380163b9ece5aa3; TS624e36da027=08b707dd67ab2000ad9aefe526c2c528695d9235096dc5f29f908ffbe5254ea28738c84ce492dd1908bdf1993b113000f7dd8643486e6ca308054d60b07e1a2a1699fb2ca85e5903a27fd7867c2be28c0cd0202861d36ddc5b0372cecff15491",
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
