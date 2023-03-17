from flask import Flask
from flask import redirect
import sys

is_prod = False
if len(sys.argv) > 1:
    is_prod = sys.argv[1] == "prod"


def create_app():
    server = Flask(__name__)
    with server.app_context():
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
    return redirect("/sale")


if __name__ == '__main__':
    print("is_prod", is_prod)
    if is_prod:
        app.run(debug=False, host="0.0.0.0")
    else:
        app.run(debug=True, port=8049)
