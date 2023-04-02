import os

# FIX for OpenBLAS blas_thread_init: pthread_create: Resource temporarily unavailable
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from flask import Flask
from flask import request
from flask import redirect
import sys
from datetime import datetime
from flask_caching import Cache

# from flask import Blueprint

server = Flask(__name__)

cache = Cache(server, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 3600})


# blueprint = Blueprint('dataframes', __name__)
@cache.cached(timeout=3600)
def load_dataframes():
    from app_map.utils import get_file_from_remote
    from app_map.utils import app_preprocess_df
    df_rent_all = app_preprocess_df(get_file_from_remote(filename="yad2_rent_df.pk"),)
    df_forsale_all = app_preprocess_df(get_file_from_remote(filename="yad2_forsale_df.pk"))
    # STATS
    def preprocess(df):
        import numpy as np
        df['price_meter'] = df['price'] / df['square_meter_build']
        df['price_meter'] = df['price_meter'].replace(np.inf, np.nan)
        df.sort_values('price_meter', ascending=False)
        return df

    df_log_rent = preprocess(get_file_from_remote("df_log_rent.pk"))
    df_log_forsale = preprocess(get_file_from_remote("df_log_forsale.pk"))

    dict_df_agg_nadlan_all = get_file_from_remote("dict_df_agg_nadlan_all.pk")
    dict_df_agg_nadlan_new = get_file_from_remote("dict_df_agg_nadlan_new.pk")
    dict_df_agg_nadlan_old = get_file_from_remote("dict_df_agg_nadlan_old.pk")
    dict_combined = dict(ALL=dict_df_agg_nadlan_all,
                         NEW=dict_df_agg_nadlan_new,
                         OLD=dict_df_agg_nadlan_old)
    date_updated = df_log_forsale['date_updated'].max().date()
    stats = dict(df_log_forsale=df_log_forsale, df_log_rent=df_log_rent, dict_combined=dict_combined, date_updated=date_updated)
    #
    sale = dict(df_forsale_all=df_forsale_all)
    rent = dict(df_rent_all=df_rent_all)

    return dict(sale=sale, rent=rent, stats=stats)


def get_stats_data():
    with server.test_request_context():
        return load_dataframes()['stats']


def get_rent_data():
    with server.test_request_context():
        return load_dataframes()['rent']['df_rent_all']


def get_sale_data():
    with server.test_request_context():
        return load_dataframes()['sale']['df_forsale_all']


# @blueprint.route('/load_dataframe/<string:object_key>')
# @cache.cached(timeout=3600)
# def load_dataframe(object_key):
#     bucket_name = 'my-s3-bucket'
#     obj = s3.get_object(Bucket=bucket_name, Key=object_key)
#     df = pd.read_csv(obj['Body'])
#     return df


def create_app(server):
    from app_map.dashboard_yad2_rent import get_dash as get_dash_rent
    server, _ = get_dash_rent(server)
    from app_map.dashboard_yad2_forsale import get_dash as get_dash_sale
    server, _ = get_dash_sale(server)
    from app_map.dashboard_stats import get_dash as get_dash_stats
    server, _ = get_dash_stats(server)

    return server


app = create_app(server)


@app.before_request
def before_request():
    # user_agent=request.headers['HTTP_USER_AGENT'], req_uri=request.headers['REQUEST_URI']
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        address = request.environ['REMOTE_ADDR']
    else:
        address = request.environ['HTTP_X_FORWARDED_FOR']  # if behind a proxy
    header_env = request.environ['HTTP_USER_AGENT']
    user_log = dict(ts=str(datetime.today().strftime("%Y-%m-%d %H:%M:%S")),
                    ip=address,
                    path=request.path,
                    user_agent=header_env)
    # curr_file_mod = datetime.today().minute // 15
    # with open(f"user_activity_log_{curr_file_mod}", "a") as f:
    #     print(",".join(user_log), flush=True, file=f)
    # idea - log into file, split by 15 minute each, write into csv file or something like that in append way.
    # after this has passed, upload it to postgres as is, in the meanti
    print("REQ::", list(user_log.values()))


@app.route("/")
def hello_world():
    # return "YES"
    return redirect("/sale")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        app.run(debug=True, port=8050)
    else:
        app.run(debug=False, port=8050)
