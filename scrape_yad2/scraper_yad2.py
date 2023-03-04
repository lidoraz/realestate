import os
import requests
from tqdm import tqdm
import time
import pandas as pd
from datetime import datetime

import sqlalchemy

from scrape_nadlan.utils_insert import get_table, create_ignore_if_exists
from scrape_yad2.utils import _get_parse_item_add_info
from scrape_yad2.config import *


def remove_dup(table, partitions, con, debug):
    partitions = [partitions] if not isinstance(partitions, list) else partitions
    partitions_str = ', '.join(partitions)
    row_id = 'rowid' if debug else 'ctid'
    q_today_remove_duplicates = f"""
    DELETE FROM {table}
    WHERE {row_id} IN(
        SELECT {row_id}
        FROM (SELECT {row_id},
        ROW_NUMBER() OVER (PARTITION BY {partitions_str}) AS rn
        FROM {table}) t
        WHERE rn > 1)
    """
    con.execute(q_today_remove_duplicates)


def escape_quote(df, cols):
    # print(cols)
    for c in cols:
        df[c] = df[c].astype(str).str.replace("'", "''")


class ScraperYad2:
    def __init__(self, url, use_cols, today_table, history_table, log_table, item_table):
        self.url = url
        self.use_cols = use_cols
        self.history_table = history_table
        self.today_table = today_table
        self.log_table = log_table
        self.item_table = item_table

    def _get_retry_json(self, p):
        res = None
        for _ in range(TRIES):
            try:
                res = requests.get(self.url.format(p))
                if res.status_code == 200:
                    break
                else:
                    print(f"Status code err, retry {_}/{TRIES}")
                    print(res)
                    time.sleep(10)
            except Exception as e:
                print(f"Caught an exception in get retry {_}/{TRIES}")
                time.sleep(10)
        if res:
            return res.json()
        return res

    def insert_today_temp(self, df, con):
        df.to_sql(name=f'{self.today_table}_temp', con=con, if_exists='append', index=False)

    def track_active(self, con):
        print("Updating log table")
        today_ids = pd.read_sql(f"Select distinct id from {self.today_table}", con)['id'].to_list()
        today_ids_s = set(today_ids)
        # case has rows, set active, not active
        logged_ids = pd.read_sql(f"Select id from {self.log_table}", con)['id'].to_list()
        logged_ids_s = set(logged_ids)

        ids_in_both = today_ids_s.intersection(logged_ids_s)
        ids_only_in_today = today_ids_s - logged_ids_s

        print('ids_in_both', len(ids_in_both))
        if len(ids_in_both):
            ids_active_str = [f"'{i}'" for i in ids_in_both]
            res = con.execute(f"DELETE FROM {self.log_table} where id in ({','.join(ids_active_str)})")
            print('DELETED - ', res)

        ids_combined = ids_only_in_today.union(ids_in_both)
        ids_str = [f"'{i}'" for i in ids_combined]
        con.execute(
            f"INSERT INTO {self.log_table} "
            f"SELECT *, true FROM {self.today_table} WHERE id in ({','.join(ids_str)})")
        # Set old ones to not-active
        inactive_ids = logged_ids_s - today_ids_s
        if len(inactive_ids):
            ids_not_active_str = [f"'{id}'" for id in inactive_ids]
            con.execute(f"UPDATE {self.log_table} SET active=false WHERE id in ({','.join(ids_not_active_str)})")
        print("Finished Updating log table!")

    def update_today(self, con, debug):
        remove_dup(f"{self.today_table}_temp", 'id', con, debug)
        con.execute(f"DROP table if exists {self.today_table}")
        # pd.read_sql(f"select * from {self.today_table}_temp", con)
        create_ignore_if_exists(con, self.today_table, sql_today_dtypes, primary_keys=["id"])
        con.execute(f"INSERT INTO {self.today_table} SELECT * FROM {self.today_table}_temp")
        con.execute(f"DROP table {self.today_table}_temp")
        remove_dup(self.history_table, ['id', 'processing_date'], con, debug)

    def _preprocess(self, df, today_str):
        df = df[df['type'] == 'ad'].copy()
        df.columns = [c.lower() for c in df.columns]
        df['processing_date'] = today_str
        res_cords = pd.DataFrame(df['coordinates'].to_list())
        df = pd.concat([df.reset_index(drop=True), res_cords.reset_index(drop=True)], axis=1)
        df = df.rename(columns=cols_renamer_today)
        df = df[cols_renamer_today.values()]
        re_digits = "(\d+)"
        df['floor'] = df['floor'].str.replace('קומת קרקע', 'קומה 0').str.extract(re_digits)[0].astype('float').astype("Int32")
        df['price'] = df['price'].str.replace(',', '').str.extract(re_digits)[0].astype('float').astype('Int64')
        df['primary_area_id'] = pd.to_numeric(df['primary_area_id'], errors="coerce")
        df['area_id'] = pd.to_numeric(df['area_id'], errors="coerce")
        return df

    def create_tables(self, con):
        con.execute(f"DROP table if exists {self.today_table}_temp")
        create_ignore_if_exists(con, f'{self.today_table}_temp', sql_today_dtypes)
        create_ignore_if_exists(con, self.history_table, sql_price_history_dtypes)
        sql_today_dtypes_log = sql_today_dtypes.copy()
        sql_today_dtypes_log['active'] = sqlalchemy.Boolean
        create_ignore_if_exists(con, self.log_table, sql_today_dtypes_log, primary_keys=["id"])
        create_ignore_if_exists(con, self.item_table, sql_items_dtypes, primary_keys=["id"])

    def insert_to_items(self, con, debug):
        # item_table = "yad2_forsale_items_add"
        ids = pd.read_sql(f"SELECT id from {self.today_table}", con)['id'].to_list()
        today = datetime.today().date()
        #
        ids_in_items = pd.read_sql(f"SELECT id from {self.item_table}", con)['id'].to_list()
        ids_to_insert = list(set(ids) - set(ids_in_items))
        print(f"Preparing to insert: {len(ids_to_insert)} items")
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(N_THREADS_ITEM_ADD) as executor:
            results = list(tqdm(executor.map(_get_parse_item_add_info, ids_to_insert), total=len(ids_to_insert)))
        results = [i for i in results if i is not None]
        df_items = pd.DataFrame(results)
        df_items['processing_date'] = today
        if debug:
            escape_quote(df_items, ['info_text', 'image_urls'])
        df_items.to_sql(self.item_table, con, if_exists='append', index=False)
        print(f"insert_to_items: Inserted to {self.item_table} {len(df_items)} items!")

    def scraper_yad2(self, con, debug=False):
        self.create_tables(con)
        res = self._get_retry_json(1)
        last_page = res['data']['pagination']['last_page']
        last_page = 3 if debug else last_page
        today_dt = datetime.today()
        df_today_history = pd.read_sql(q_history_last_price.format(self.history_table), con)
        df = None
        for p in tqdm(range(1, last_page + 1)):
            try:
                data = self._get_retry_json(p)
                data = data.get('data')
                if data is None:  # [ for x in df['row_4'].tolist()]
                    print(f"CAUTION - Could not fetch data for part {p}")
                df = pd.DataFrame.from_dict(data['feed']['feed_items'])
                df = self._preprocess(df, today_dt)
                if debug:
                    escape_quote(df, [k for k, v in sql_today_dtypes.items() if v == sqlalchemy.String])
                self.log_history(df, df_today_history, con)
                self.insert_today_temp(df, con)
            except Exception as e:
                print("Caught an exception in loop! ", e)
                if debug:
                    raise e
        # update only if there was a change(prob was)
        if df is None:
            return
        self.update_today(con, debug)
        self.track_active(con)
        self.insert_to_items(con, debug)

    def _check_exists(self, today_str, con):
        cnt_today = pd.read_sql(f"SELECT count(*) from {self.history_table} where processing_date = '{today_str}'",
                                con).squeeze()
        if cnt_today > 0:
            raise ValueError(f"Data from {today_str} already saved in db, total {cnt_today} rows")

    def log_history(self, df, df_today_history, con):
        # will dump only if a price of an id has changed from its current logged price, to save space and efficiency
        minimum_cols = sql_price_history_dtypes.keys()
        df = df[minimum_cols].copy()
        merged = df[['id', 'price']].merge(df_today_history, left_on='id', right_on='id', how='left')
        merged['last_price'] = merged['last_price'].astype(float)
        # cond with equal, and equal nan, special case
        equal_cond = (merged['price'] == merged['last_price'])
        equal_nan_cond = (merged['price'].isna() & merged['last_price'].isna())
        ids_not_changed = merged[equal_cond | equal_nan_cond]['id'].to_list()
        df = df[~df['id'].isin(ids_not_changed)]
        df.to_sql(name=self.history_table, con=con, if_exists='append', index=False, dtype=history_dtype)
