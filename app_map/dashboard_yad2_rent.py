import dash
from app_map.utils import *
from app_map.util_layout import get_layout
from app_map.utils_callbacks import add_callbacks

BASE_URL = "rent"


def get_dash(server):
    df_all = get_df_with_prod(filename="yad2_rent_df.pk")
    df_all = app_preprocess_df(df_all)
    rent_config_default = {"price-from": 1_000, "price-to": 6_000, "median-price-pct": None,
                           "price-min": 500, "price-max": 10_000,
                           "switch-median": False,
                           "discount-price-pct": -0.05,
                           "ai_pct": None,
                           "price_step": 500,
                           "price_mul": 1,  # 1e3,
                           "with_nadlan": False,  # Work around for missing nadlan db in remote
                           "name": BASE_URL,
                           "data": df_all
                           }

    df_all.query('-0.89 <price_pct < -0.05').to_csv('df_rent.csv')
    app = dash.Dash(server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], title="Rent",
                    url_base_pathname=f'/{BASE_URL}/')

    app.layout = get_layout(rent_config_default)
    add_callbacks(app, rent_config_default)
    return server, app


if __name__ == '__main__':
    _, app = get_dash(True)
    app.run_server(debug=True, port=8048)
