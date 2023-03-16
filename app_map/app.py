from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import dash
import sys

from app_map.utils import get_df_with_prod, app_preprocess_df

is_prod = False
if len(sys.argv) > 1:
    is_prod = sys.argv[1] == "prod"

# https://dash.plotly.com/urls
app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
# app.layout = html.Div([
#     # html.H1('Multi-page app with Dash Pages'),
#
#     html.Div(
#         [
#             html.Div(
#                 dcc.Link(
#                     f"{page['name']} - {page['path']}", href=page["relative_path"]
#                 )
#             )
#             for page in dash.page_registry.values()
#         ]
#     ),
#
#     dash.page_container
# ])

if __name__ == '__main__':
    # from app_map.pages.rent import df_all, rent_config_default
    from app_map.utils_callbacks import add_callbacks

    rent_config_default = {"price-from": 1_000, "price-to": 6_000, "median-price-pct": None,
                           "price-min": 500, "price-max": 10_000,
                           "switch-median": False,
                           "discount-price-pct": -0.05,
                           "ai_pct": None,
                           "price_step": 500,
                           "price_mul": 1,  # 1e3,
                           "with_nadlan": False  # Work around for missing nadlan db in remote
                           }

    df_all = get_df_with_prod(True, filename="yad2_rent_df.pk")
    df_all = app_preprocess_df(df_all)
    app.config.suppress_callback_exceptions = True
    add_callbacks(app, df_all, rent_config_default)
    if is_prod:
        app.run_server(debug=True, host="0.0.0.0")
    else:
        app.run_server(debug=True)
