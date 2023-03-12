import os
import sys
import dash
from app_map.utils import *
from app_map.util_layout import get_layout
from app_map.utils_callbacks import add_callbacks

is_prod = False
if len(sys.argv) > 1:
    is_prod = sys.argv[1] == "prod"

rent_config_default = {"price-from": 1_000, "price-to": 6_000, "median-price-pct": None,
                       "price-min": 500, "price-max": 10_000,
                       "switch-median": False,
                       "discount-price-pct": -0.05,
                       "ai_pct": None,
                       "price_step": 500,
                       "price_mul": 1,  # 1e3,
                       "with_nadlan": False  # Work around for missing nadlan db in remote
                       }

df_all = get_df_with_prod(is_prod, filename="yad2_rent_df.pk")
df_all = app_preprocess_df(df_all)

df_all.query('-0.89 <price_pct < -0.05').to_csv('df_rent.csv')
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], title="Rent")

app.layout = get_layout(rent_config_default)
add_callbacks(app, df_all, rent_config_default)

# https://python.plainenglish.io/how-to-create-a-model-window-in-dash-4ab1c8e234d3

#
# @app.callback(
#     Output('datatable-interactivity', "editable"),
#     # [Output("datatable-rfStats", "data"), Output("datatable-rfStats", "selected_rows")],
#     [Input("datatable-interactivity", "active_cell"), State("datatable-interactivity", "data")]  # + plot_dev_lvl_filter_inputs
# )
# def handle_table_row_select(row, data):
#     # print("handle_table_row_select", row)
#     # print(row, data)
#     if row is not None:
#         print("SELECTED:", data[row['row']])
#     return dash.no_update
#     # filtered_df.sort_values(by=['lastUpdated']).to_dict('records'), [row_id]


if __name__ == '__main__':
    if is_prod:
        app.run_server(debug=True, host="0.0.0.0")
    else:
        app.run_server(debug=True)
