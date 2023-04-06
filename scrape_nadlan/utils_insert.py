import argparse
import json
import os

from sqlalchemy import Column, Table, MetaData, create_engine


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


def load_vault():
    path = os.path.expanduser('~')
    path = os.path.join(path, '.ssh', "creds_postgres.json")
    with open(path) as f:
        c = json.load(f)
    for k, v in c.items():
        os.environ[k] = str(v)


def get_engine():
    load_vault()
    eng = create_engine(
        f"postgresql://{os.environ['PGUSER']}:{os.environ['PGPASSWORD']}@{os.environ['PGHOST']}:{os.environ['PGPORT']}/{os.environ['PGDATABASE']}")
    return eng


def get_telegram_creds():
    load_vault()
    bot_id = os.environ.get("TELEGRAM_TOKEN")
    channel_id = os.environ.get("TELEGRAM_CHANNEL")
    assert bot_id
    assert channel_id
    return bot_id, channel_id


def send_telegram_msg(msg):
    bot_id, channel_id = get_telegram_creds()
    import requests
    url = f"https://api.telegram.org/bot{bot_id}/sendMessage?chat_id={channel_id}&text={msg}&parse_mode=HTML"
    res = requests.get(url)
    print(f"Sent with code: {res.status_code}")

