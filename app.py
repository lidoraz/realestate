import os

# FIX for OpenBLAS blas_thread_init: pthread_create: Resource temporarily unavailable
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from flask import Flask
from flask import request
from flask import redirect
import sys
from datetime import datetime
from flask_caching import Cache
import json

# from flask import Blueprint

server = Flask(__name__)

cache = Cache(server, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 3600})

# Logic - first time - download. then check for time, if its over 22:00, download again, check time in header, to update last update date. otherwise, use cache data
cache_dict = {}
updated_path = "resources/updated_at.json"

from datetime import timedelta


@cache.cached(timeout=50)
def get_updated_at():
    print("Reloading from disk..")
    if not os.path.exists(updated_path):
        return None
    with open(updated_path, 'r') as f:
        # TODO ADD TZ change here
        updated_at = datetime.fromisoformat(json.loads(f.read())['updatedAt'])
    return updated_at


def is_cache_ok(hours_diff=24):
    updated_at = get_updated_at()
    if updated_at is None:
        return False
    remote_diff = (datetime.now() - updated_at).total_seconds() / 3600
    if remote_diff < hours_diff:  # check remote
        return True
    print(f"Diff is: {remote_diff} hours, downloading from remote")
    return False


def download_files(filenames):
    from app_map.utils import download_from_remote
    dt_modified = None
    for filename in filenames:
        dt_modified = download_from_remote(filename)
    with open(updated_path, "w") as f:
        json.dump({"updatedAt": dt_modified}, f)
        global cache_dict
        cache_dict['updatedAt'] = dt_modified


def _preprocess_and_load():
    print("Loading from load_dataframes")
    from app_map.utils import read_pk
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
    cache_dict = dict(sale=sale, rent=rent, stats=stats)
    return cache_dict


# @cache.cached(timeout=3600)
def load_dataframes():
    filenames = ["df_nadlan_recent.pk",
                 "yad2_rent_df.pk",
                 "yad2_forsale_df.pk",
                 "fig_timeline_new_vs_old.pk",
                 "dict_df_agg_nadlan_all.pk",
                 "dict_df_agg_nadlan_new.pk",
                 "dict_df_agg_nadlan_old.pk",
                 "df_log_rent.pk",
                 "df_log_forsale.pk"]
    if not is_cache_ok():
        download_files(filenames)
        _preprocess_and_load()
    global cache_dict
    if len(cache_dict) == 0:
        _preprocess_and_load()
    return cache_dict


def get_stats_data():
    with server.test_request_context():
        return load_dataframes()['stats']


def get_rent_data():
    with server.test_request_context():
        return load_dataframes()['rent']['df_rent_all']


def get_sale_data():
    with server.test_request_context():
        return load_dataframes()['sale']['df_forsale_all']


def create_app(server):
    from app_map.dashboard_yad2_rent import get_dash as get_dash_rent
    server, _ = get_dash_rent(server)
    from app_map.dashboard_yad2_forsale import get_dash as get_dash_sale
    server, _ = get_dash_sale(server)
    from app_map.dashboard_stats import get_dash as get_dash_stats
    server, _ = get_dash_stats(server)

    return server


app = create_app(server)


# @app.before_request
# def before_request():
#     # user_agent=request.headers['HTTP_USER_AGENT'], req_uri=request.headers['REQUEST_URI']
#     if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
#         address = request.environ['REMOTE_ADDR']
#     else:
#         address = request.environ['HTTP_X_FORWARDED_FOR']  # if behind a proxy
#     header_env = request.environ['HTTP_USER_AGENT']
#     user_log = dict(ts=str(datetime.today().strftime("%Y-%m-%d %H:%M:%S")),
#                     ip=address,
#                     path=request.path,
#                     user_agent=header_env)
#     print("REQ::", list(user_log.values()))


@app.route("/")
def hello_world():
    # return "YES"
    return redirect("/sale")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        app.run(debug=True, port=8050)
    else:
        app.run(debug=False, port=8050)
