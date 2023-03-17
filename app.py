import os

from flask import Flask
from flask import redirect
import sys


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


@app.route("/")
def hello_world():
    # return "YES"
    return redirect("/sale")


if __name__ == '__main__':
    app.run(debug=False, port=8050)
    # host = os.environ.get("DEBUG")
    # if is_prod:
    #     # from waitress import serve
    #     # serve(app, host="0.0.0.0")
    #     app.run(host=host, port=8050)
    # else:
    #     app.run(debug=True, port=8050)
