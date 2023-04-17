import os

# FIX for OpenBLAS blas_thread_init: pthread_create: Resource temporarily unavailable
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from flask import Flask
from flask import redirect
import sys
from datetime import datetime
from flask_caching import Cache
import json
from apscheduler.schedulers.background import BackgroundScheduler


from app_map.persistance_utils import load_dataframes, download_remote

server = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.add_job(download_remote, 'cron', hour=20, minute=0)
download_remote(force_download=False)
scheduler.start()
cache = Cache(server, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 3600})
updated_path = "resources/updated_at.json"


@cache.cached(timeout=50)
def get_updated_at():
    print("Reloading from disk..")
    if not os.path.exists(updated_path):
        return None
    with open(updated_path, 'r') as f:
        # TODO ADD TZ change here
        updated_at = datetime.fromisoformat(json.loads(f.read())['updatedAt'])
    return updated_at


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


@app.route("/")
def hello_world():
    # return "YES"
    return redirect("/sale")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        app.run(debug=True, port=8050)
    else:
        app.run(debug=False, port=8050)
