# Workaround for python in windows...
from os.path import dirname
import sys

file_dir = dirname(dirname(__file__))
sys.path.append(file_dir)

from scrape_nadlan.config import *
from sqlalchemy import sql, select
from scrape_nadlan.utils_insert import *
from scrape_nadlan.Scraper.utils import filter_files, read_files
import pandas as pd
import numpy as np


def _fix_invalid_cords(df):
    df.loc[(df['corX'] == 0) & (df['corY'] == 0), 'lat'] = np.nan
    df.loc[(df['corX'] == 0) & (df['corY'] == 0), 'long'] = np.nan


def preprocessing(df, drop_duplicates, dropna):
    df['tarIska'] = pd.to_datetime(df['tarIska'], format="%d/%m/%Y").dt.date
    df['gush_full'] = df['gush']
    gush_temp = df['gush_full'].str.split('-')
    df['gush'] = gush_temp.str[0].astype(int)
    df['helka'] = gush_temp.str[1].astype(int)
    df['t_helka'] = gush_temp.str[2].astype(int)
    lat, long = trans_itm_to_wgs84.transform(df['corX'], df['corY'])
    df['lat'] = lat
    df['long'] = long
    _fix_invalid_cords(df)
    df['mcirMozhar'] = df['mcirMozhar'].str.replace(',', '').astype('Int32')
    df['mcirMorach'] = df['mcirMorach'].str.replace(',', '').astype('Int32')
    df['hanaya'] = df['hanaya'].str.split(' ').str[0].astype(int)
    df['lblKoma'].astype(str).str.replace('קומת קרקע', '0').astype(float).astype(int)

    df = df.rename(columns=columns_rename)
    if drop_duplicates:
        len_b = len(df)
        df = df.drop_duplicates(subset=primary_keys)
        print(f"DROP DUPLICATES: Before: {len_b}, After: {len(df)}")
    if dropna:
        len_b = len(df)
        df = df.dropna(subset=primary_keys)
        print(f"DROPNA Before: {len_b}, After: {len(df)}")

    df = df[columns_rename.values()]
    return df


def insert_to_postgres_db(dt):
    eng = get_engine()
    nadlan_trans_tbl = create_ignore_if_exists(eng, tbl_name, columns_alchemy, primary_keys)

    file_lst = filter_files(dt)

    df = read_files(file_lst, True)
    df = preprocessing(df, drop_duplicates=True, dropna=True)
    df = check_exists(df, nadlan_trans_tbl, eng, 'trans_date')
    _insert_not_safe(df, eng)


def _warp(q):
    return sql.text(q)


def check_exists(df, tbl, eng, dt_col):
    len_b = len(df)
    with eng.connect() as conn:
        stmt_cols = [getattr(tbl.c, pk) for pk in primary_keys]
        unique_days = df[dt_col].unique()
        stmt = select(*stmt_cols).where(getattr(tbl.c, dt_col).in_(unique_days))
        df_in_db = pd.read_sql(stmt, conn)
        df_m = df.merge(df_in_db, how='left', indicator=True)
        df = df_m[df_m['_merge'] != 'both'].drop(columns='_merge')
    if len(df) < len_b:
        print(f"Rows to insert after checking exists: {len(df)}, removed total {len_b - len(df)}")
    return df


def _insert_not_safe(df, eng):
    # Not checking if exists, need to combine with filter out first
    with eng.connect() as conn:
        # conn.execute(_warp(f"DROP TABLE {tbl_name}"))
        # df_in_db = pd.read_sql(sql.text(f"SELECT * from {tbl_name} limit 10"), conn)
        res = df.to_sql(tbl_name, if_exists="append", index=False, con=conn)
        conn.commit()
    print(f"Inserted {res} rows from df {len(df)}")


if __name__ == '__main__':
    # _dt = '2023-01-01'
    # _dt = '2023'
    _dt = None
    # if _dt is None:
    #     _dt = get_args()

    insert_to_postgres_db(_dt)
