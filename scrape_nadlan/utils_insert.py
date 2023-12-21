import argparse
import os
import requests
import time
from requests.exceptions import RequestException
from sqlalchemy import Column, Table, MetaData
from ext.env import load_vault

load_vault()
bot_id = os.getenv('TELEGRAM_BOT_ID') or os.getenv("TELEGRAM_TOKEN")
channel_id = os.getenv("TELEGRAM_CHANNEL")
assert bot_id
assert channel_id


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("dt")
    args = parser.parse_args()
    return args.dt


def create_ignore_if_exists(con, tbl_name, cols_types, primary_keys=()):
    metadata_obj = MetaData()
    tbl = get_table(tbl_name, cols_types, metadata_obj, primary_keys=primary_keys)
    metadata_obj.create_all(con)
    return tbl


def get_table(tbl_name, columns_alchemy, metadata_obj, primary_keys=()):
    columns = [Column(name, col_type, primary_key=True if name in primary_keys else False) for
               (name, col_type) in columns_alchemy.items()]
    nadlan_trans_tbl = Table(tbl_name,
                             metadata_obj,
                             *columns)
    return nadlan_trans_tbl


def safe_send(url, params=None, tries=10):
    for _ in range(tries):
        try:
            res = requests.get(url, params=params)
            print(f"Sent with code: {res.status_code}")
            return
        except RequestException as e:
            time.sleep(1)
    print("Failed to send msg after {}".format(tries))


def send_telegram_msg(msg):
    from ext.publish import send_to_telegram_channel
    send_to_telegram_channel(msg, channel_id, bot_id)
