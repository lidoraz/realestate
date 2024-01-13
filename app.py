import os
import logging
from app_map.telegram_bot import serve_bot_threaded
from ext.db_user import add_user_activity_records

# from flask_basicauth import BasicAuth
# Flask-BasicAuth

os.environ[
    'OPENBLAS_NUM_THREADS'] = '1'  # fixes OpenBLAS blas_thread_init: pthread_create: Resource temporarily unavailable

from flask import Flask, redirect
import sys
from apscheduler.schedulers.background import BackgroundScheduler

from app_map.persistance_utils import is_cache_ok, loop_until_remote_ready, download_remote

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
## the process starts at 19 UTC and usually finishes by 18:30
scheduler.add_job(loop_until_remote_ready, 'cron', hour=18, minute=20)
if not is_cache_ok():
    download_remote(block=True)
scheduler.start()


def create_app(server):
    from app_map.dashboard_yad2_forsale import get_dash as get_dash_sale
    server, _ = get_dash_sale(server)
    from app_map.dashboard_yad2_rent import get_dash as get_dash_rent
    server, _ = get_dash_rent(server)
    from app_map.dashboard_stats import get_dash as get_dash_stats
    server, _ = get_dash_stats(server)
    from app_map.dashboard_neighborhood import get_dash as get_dash_neightbor
    server, _ = get_dash_neightbor(server)
    from app_map.register_user import get_dash as get_dash_register_bot
    server, _ = get_dash_register_bot(server)

    is_prod = os.getenv("PRODUCTION", False)
    if is_prod:
        print(f"TELEGRAM BOT IS STARTING: PRODUCTION={is_prod}")
        serve_bot_threaded()
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


from flask import Flask, request
from datetime import datetime

# Dictionary to store user sessions
sessions = {}


# filter messages between first and last which have "_dash" in their endpoint
def _filter_between_user_activity(user_data_lst):
    length = len(user_data_lst)
    if length > 2:
        user_data_lst = [d for idx, d in enumerate(user_data_lst) \
                         if idx in (0, length - 1) or (d.get('endpoint') is not None and '_dash' not in d['endpoint'])]
    return user_data_lst


# --/sale/_dash-update-component /sale/_dash-component-suites
# Function to check inactivity and log sessions
def check_inactivity(inactivity_sec=300):
    current_time = datetime.utcnow()
    # Iterate through the sessions and check inactivity
    for ip, payload in sessions.copy().items():
        last_interact = payload["last_interact"]
        if (current_time - last_interact).total_seconds() > inactivity_sec:  # 300:  # 5 minutes of inactivity
            user_data_lst = payload['data']
            user_data_lst = _filter_between_user_activity(user_data_lst)
            add_user_activity_records(user_data_lst)
            del sessions[ip]


def process_json_req():
    import json
    try:
        req_json = json.loads(request.data)
        # do something with json
    except Exception as e:
        req_json = None
    return req_json


# Middleware to handle user interactions
@app.before_request
def before_request():
    # get ip if behind a proxy, or regular
    ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ['REMOTE_ADDR'])
    telegram_id = request.args.get('telegram_id')
    # if telegram_id is None:
    #     print("DDD", ip)
    #     # Later will handle users without id with a cookie
    #     return
    asset_id = request.args.get('asset_id')
    asset_type = request.path.split('/')[1] if '/' in request.path else None
    # url = request.url
    user_agent = request.headers.get('User-Agent')
    # ip = request.remote_addr
    # Add first interaction time
    # maybe session length in time?
    # Update session data
    if ip not in sessions:
        print(f"""FIRST USER ACQ:: {ip}""")
        sessions[ip] = {'last_interact': None, 'data': []}
        session_rn = 1
    else:
        prev_rn = sessions[ip]['data'][-1]['session_rn']
        session_rn = prev_rn + 1

    data = {'telegram_id': telegram_id,
            'asset_id': asset_id,
            'asset_type': asset_type,  # already in endpoint.
            'endpoint': request.endpoint,
            'dt': datetime.utcnow(),
            'ip': ip,
            'user_agent': user_agent,
            'session_rn': session_rn
            }
    sessions[ip]['last_interact'] = datetime.utcnow()
    sessions[ip]['data'].append(data)


# Schedule the check_inactivity function to run every X minute
scheduler.add_job(check_inactivity, 'interval', minutes=5)

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
