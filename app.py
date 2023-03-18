import os

from flask import Flask
from flask import request
from flask import redirect
import sys
from datetime import datetime


def create_app():
    server = Flask(__name__)
    from app_map.dashboard_yad2_rent import get_dash as get_dash_rent
    server, _ = get_dash_rent(server)
    from app_map.dashboard_yad2_forsale import get_dash as get_dash_sale
    server, _ = get_dash_sale(server)
    from app_map.dashboard_stats import get_dash as get_dash_stats
    server, _ = get_dash_stats(server)
    return server


app = create_app()


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
