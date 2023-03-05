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


def get_engine():
    path = os.path.expanduser('~')
    path = os.path.join(path, '.ssh', "creds_postgres.json")
    with open(path) as f:
        c = json.load(f)
    eng = create_engine(f"postgresql://{c['user']}:{c['passwd']}@{c['host']}:{c['port']}/{c['db']}")
    return eng
