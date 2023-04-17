from datetime import datetime
import json
import os
import threading
import pickle

updated_path = "resources/updated_at.json"

bucket = "real-estate-public"
pre_path = f"resources/"
is_downloading = False
cache_dict = {}

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
        dt_modified = keys[0]['LastModified'].replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")
    return dt_modified


def download_from_remote(s3_client, filename):
    path_file = pre_path + filename
    print(f"{datetime.now()}, Downloading file {filename}")
    s3_client.download_file(bucket, path_file, path_file)


def read_pk(filename):
    with open(f"resources/{filename}", "rb") as f:
        return pickle.load(f)


def get_diff(updated_at):
    return (datetime.now() - updated_at).total_seconds() / 3600


def is_cache_ok(hours_diff=24):
    try:
        with open(updated_path, 'r') as f:
            # TODO ADD TZ change here
            updated_at = datetime.fromisoformat(json.loads(f.read())['updatedAt'])
    except Exception as e:
        return False
    diff = get_diff(updated_at)
    print(f"diff from remote - {diff:.2f} < {hours_diff}")
    return diff < hours_diff


def get_updated_at():
    with open(updated_path, 'r') as f:
        # TODO ADD TZ change here
        updated_at = datetime.fromisoformat(json.loads(f.read())['updatedAt'])
        return updated_at


def download_files(filenames):
    s3_client = get_aws_session().client('s3')
    updated_at = get_updated_at()
    diff_h = get_diff(updated_at)
    print(f"Downloading from remote, diff is {diff_h:.1f} hours")
    for filename in filenames:
        download_from_remote(s3_client, filename)
    dt_modified = check_time_modified(get_aws_session(), filenames[0])
    with open(updated_path, "w") as f:
        json.dump({"updatedAt": dt_modified}, f)
    global is_downloading
    is_downloading = False


def _preprocess_and_load():
    print("Loading from load_dataframes")
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
    global cache_dict
    cache_dict.update(dict(sale=sale, rent=rent, stats=stats))


def download_remote(force_download=True):
    if force_download or not is_cache_ok():
        download_files(filenames)
        global cache_dict
        cache_dict = {}
    else:
        print("Not downloading")


def load_dataframes():
    # threading.Thread(target=download_files, args=(filenames,)).start()
    if len(cache_dict) == 0:
        _preprocess_and_load()
    return cache_dict
