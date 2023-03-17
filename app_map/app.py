import dash_auth
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
from VALID_USERNAME_PASSWORD_PAIRS import VALID_USERNAME_PASSWORD_PAIRS

# CAN PRINT THIS WITH auth.get_user_data()
# auth = dash_auth.BasicAuth(
#     app,
#     VALID_USERNAME_PASSWORD_PAIRS
# )
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
    is_prod = False
    df_all = get_df_with_prod(is_prod, filename="yad2_rent_df.pk")
    df_all = app_preprocess_df(df_all)

    # # TODO NEED TO ADD INTO ALL id= prefix of sale / rent  😩
    # df_all_f = get_df_with_prod(is_prod, filename="yad2_forsale_df.pk")
    # df_all_f = app_preprocess_df(df_all_f)

    app.config.suppress_callback_exceptions = True
    from app_map.pages.rent import rent_config_default
    add_callbacks(app, df_all, rent_config_default)
    if is_prod:
        app.run_server(debug=True, host="0.0.0.0")
    else:
        app.run_server(debug=True)
