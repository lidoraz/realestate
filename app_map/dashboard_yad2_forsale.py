import dash
import dash_bootstrap_components as dbc
from app_map.util_layout import get_layout
from app_map.utils_callbacks import add_callbacks

BASE_URL = "sale"


def get_dash(server):
    from app_map.persistance_utils import get_sale_data
    app = dash.Dash(server=server,
                    external_stylesheets=[dbc.themes.BOOTSTRAP], title="Sale", url_base_pathname=f'/{BASE_URL}/')
    # df_all = get_file_from_remote(filename="yad2_forsale_df.pk")
    # df_all = app_preprocess_df(df_all)
    # df_all.query('-0.89 <price_pct < -0.05').to_csv('df_forsale.csv')

    forsale_config_default = {"price-from": 500, "price-to": 10_000, "median-price-pct": -0.2,
                              "price-min": 500, "price-max": 10_000,
                              "switch-median": True,
                              "discount-price-pct": None,
                              "ai_pct": None,
                              "price_step": 50,
                              "price_mul": 1e3,  # 1e6,
                              "with_nadlan": True,
                              "name": BASE_URL,
                              "func_data": get_sale_data
                              }
    app.layout = get_layout(forsale_config_default)
    add_callbacks(app, forsale_config_default)
    return server, app


# https://python.plainenglish.io/how-to-create-a-model-window-in-dash-4ab1c8e234d3


if __name__ == '__main__':
    _, app = get_dash(True)
    app.run_server(debug=True, port=8049)
