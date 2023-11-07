import os
import logging

# from flask_basicauth import BasicAuth
# Flask-BasicAuth

os.environ[
    'OPENBLAS_NUM_THREADS'] = '1'  # fixes OpenBLAS blas_thread_init: pthread_create: Resource temporarily unavailable

from flask import Flask, redirect
import sys
from apscheduler.schedulers.background import BackgroundScheduler

from app_map.persistance_utils import is_cache_ok, check_download, download_remote

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

# multiple jobs are created because we want to update as soon as etl finishes
## the process starts at 19 UTC and usually finishes by 19:40
scheduler.add_job(check_download, 'cron', hour=19, minute=40)
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
    from app_map.dashboard_neighborhood import get_dash as get_dash_neightbor
    server, _ = get_dash_neightbor(server)

    return server


app = create_app(server)


# app.config['BASIC_AUTH_USERNAME'] = '1'
# app.config['BASIC_AUTH_PASSWORD'] = '2'
# app.config['BASIC_AUTH_FORCE'] = True
# class NotBasicAuth(BasicAuth):
#     def check_credentials(self, username, password):
#
#         return super().check_credentials(username, password)


# basic_auth = NotBasicAuth(app)
#
#
@app.route('/')
# @basic_auth.required
def hello_world():
    return redirect("/sale")


#
#
# @app.before_request
# @basic_auth.required
# def before_request_callback():
#     print("before request")


# from app_map.api import get_data
#
#
# @app.route('/get_data', methods=['POST'])
# def _get_data():
#     return get_data()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        app.run(debug=True, port=8050)
    else:
        app.run(debug=False, port=8050)
