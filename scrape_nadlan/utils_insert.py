import argparse
from sqlalchemy import Column, Table


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("dt")
    args = parser.parse_args()
    return args.dt


def create_ignore_exists():
    pass


def get_table(tbl_name, columns_alchemy, metadata_obj, primary_keys=()):
    columns = [Column(name, col_type, primary_key=True if name in primary_keys else False) for
               (name, col_type) in columns_alchemy.items()]
    nadlan_trans_tbl = Table(tbl_name,
                             metadata_obj,
                             *columns)
    return nadlan_trans_tbl
