import os
import logging

# FIX for OpenBLAS blas_thread_init: pthread_create: Resource temporarily unavailable
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from flask import Flask, redirect
import sys
from apscheduler.schedulers.background import BackgroundScheduler

from app_map.persistance_utils import download_remote, is_cache_ok

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
server = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.add_job(download_remote, 'cron', hour=0, minute=0)
if not is_cache_ok():
    download_remote(block=True)
scheduler.start()


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
