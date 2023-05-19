import time
from datetime import datetime
import json
import os
import pickle
import logging

LOGGER = logging.getLogger()
updated_path = "resources/updated_at.json"

bucket = "real-estate-public"
pre_path = f"resources/"
is_downloading = False
cache_dict = {}
_last_loaded = 0
_updated_at = datetime.fromisoformat("1970-01-01")

filenames = ["df_nadlan_recent.pk",
             "yad2_rent_df.pk",
             "yad2_forsale_df.pk",
             "fig_timeline_new_vs_old.pk",
             "dict_df_agg_nadlan_all.pk",
             "dict_df_agg_nadlan_new.pk",
             "dict_df_agg_nadlan_old.pk",
             "df_log_rent.pk",
             "df_log_forsale.pk"]


def get_aws_session():
    import boto3
    session = boto3.Session(
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        region_name="eu-west-2")
    return session


def check_time_modified(session, filename):
    path_file = pre_path + filename
    keys = session.client('s3').list_objects(Bucket=bucket, Prefix=path_file).get('Contents')
    dt_modified = None
    if keys:
        dt_modified = datetime.isoformat(keys[0]['LastModified'])
    return dt_modified


def download_from_remote(s3_client, filename):
    path_file = pre_path + filename
    LOGGER.info(f"{datetime.now()}, Downloading file {filename}")
    s3_client.download_file(bucket, path_file, path_file)


def read_pk(filename):
    with open(f"resources/{filename}", "rb") as f:
        return pickle.load(f)


def get_diff(updated_at):
    return (datetime.now(updated_at.tzinfo) - updated_at).total_seconds() / 3600


def is_cache_ok(hours_diff=24):
    updated_at = get_updated_at()
    if updated_at:
        diff = get_diff(updated_at)
        LOGGER.debug(f"diff from remote - {diff:.2f} < {hours_diff}")
        return diff < hours_diff
    return False


def get_updated_at():
    global _last_loaded, _updated_at
    ts = time.time()
    if ts - _last_loaded > 50:
        LOGGER.debug(f"Reloading from file past: {_updated_at=}")
        try:
            with open(updated_path, 'r') as f:
                _updated_at = datetime.fromisoformat(json.loads(f.read())['updatedAt'])
                _last_loaded = ts
                return _updated_at
        except Exception as e:
            return False
    else:
        LOGGER.debug(f"Using cache {str(_updated_at)}")
        return _updated_at


def download_files(filenames):
    session = get_aws_session()
    dt_modified = check_time_modified(session, filenames[0])
    updated_at = get_updated_at()
    txt = "Downloading from remote"
    if updated_at:
        diff_h = get_diff(updated_at)
        txt += f", diff is {diff_h:.1f} hours"
    LOGGER.info(txt)
    for filename in filenames:
        download_from_remote(session.client('s3'), filename)
    global is_downloading
    is_downloading = False
    LOGGER.info("Finished downloading")
    cache_dict.clear()   # needed to force reload the datasets
    with open(updated_path, "w") as f:
        json.dump({"updatedAt": dt_modified}, f)


def _preprocess_and_load():
    LOGGER.info("Loading from load_dataframes")
    from app_map.utils import app_preprocess_df, preprocess_stats
    df_rent_all = app_preprocess_df(read_pk("yad2_rent_df.pk"))
    df_forsale_all = app_preprocess_df(read_pk("yad2_forsale_df.pk"))
    fig_timeline_new_vs_old = read_pk("fig_timeline_new_vs_old.pk")
    dict_df_agg_nadlan_all = read_pk("dict_df_agg_nadlan_all.pk")
    dict_df_agg_nadlan_new = read_pk("dict_df_agg_nadlan_new.pk")
    dict_df_agg_nadlan_old = read_pk("dict_df_agg_nadlan_old.pk")
    dict_combined = dict(ALL=dict_df_agg_nadlan_all,
                         NEW=dict_df_agg_nadlan_new,
                         OLD=dict_df_agg_nadlan_old)
    df_log_rent = preprocess_stats(read_pk("df_log_rent.pk"))
    df_log_forsale = preprocess_stats(read_pk("df_log_forsale.pk"))

    date_updated = df_log_forsale['date_updated'].max().date()
    stats = dict(df_log_forsale=df_log_forsale, df_log_rent=df_log_rent, dict_combined=dict_combined,
                 fig_timeline_new_vs_old=fig_timeline_new_vs_old,
                 date_updated=date_updated)
    #
    sale = dict(df_forsale_all=df_forsale_all)
    rent = dict(df_rent_all=df_rent_all)
    cache_dict.update(dict(sale=sale, rent=rent, stats=stats))


def download_remote(block=False):
    global is_downloading
    if not is_downloading:
        import threading
        is_downloading = True
        if block:
            LOGGER.info("Started downloading blocked")
            download_files(filenames)
        else:
            LOGGER.info("Started downloading with thread")
            threading.Thread(target=download_files, args=(filenames,)).start()
        # Reset cache, forces reload


def load_dataframes():
    if not is_cache_ok():
        download_remote()
    if len(cache_dict) == 0:
        _preprocess_and_load()
    return cache_dict


def get_stats_data():
    return load_dataframes()['stats']


def get_rent_data():
    return load_dataframes()['rent']['df_rent_all']


def get_sale_data():
    return load_dataframes()['sale']['df_forsale_all']
