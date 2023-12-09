import requests
import time


def send_to_telegram_channel(msg, group_id, bot_id):
    params = {
        "chat_id": group_id,
        "text": msg,
        "parse_mode": "HTML",
    }
    url = "https://api.telegram.org/bot{}/sendMessage".format(bot_id)
    safe_send(url, params=params)
    print(f"Telegram: sent to {group_id=}: {msg}")


def safe_send(url, params=None, tries=10):
    for _ in range(tries):
        try:
            res = requests.get(url, params=params)
            print(f"Sent with code: {res.status_code}")
            return
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
