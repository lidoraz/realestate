import requests
import time
import os
from ext.env import load_vault
load_vault()
is_prod = os.getenv("PRODUCTION", False)


def send_to_telegram_channel(msg, group_id, bot_id):
    params = {
        "chat_id": group_id,
        "text": msg,
        "parse_mode": "HTML",
    }
    url = "https://api.telegram.org/bot{}/sendMessage".format(bot_id)
    if is_prod:
        res = safe_send(url, params=params)
        print(f"<PROD> Telegram: sent to {group_id=}:\n{msg}")
    else:
        print(f"<NOT PROD> Telegram: sent to {group_id=}:\n{msg}")
        res = True
    return res


def safe_send(url, params=None, tries=10):
    for _ in range(tries):
        try:
            res = requests.get(url, params=params)
            print(f"Sent with code: {res.status_code}")
            return res
        except requests.exceptions.RequestException as e:
            time.sleep(1)
    print("Failed to send msg after {}".format(tries))


BUCKET_NAME = 'real-estate-public'


def put_object_in_bucket(path):
    import boto3
    session = boto3.Session()
    s3 = session.resource('s3')
    buck = s3.Bucket(BUCKET_NAME)
    print(f"Uploading file:: {path} bucket: {BUCKET_NAME}")
    buck.upload_file(path, path)
