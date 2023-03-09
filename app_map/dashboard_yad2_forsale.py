import dash
import dash_bootstrap_components as dbc
import sys
from app_map.util_layout import get_layout
from app_map.utils import get_df_with_prod, app_preprocess_df
from app_map.utils_callbacks import add_callbacks

is_prod = False
if len(sys.argv) > 1:
    is_prod = sys.argv[1] == "prod"

df_all = get_df_with_prod(False, filename="yad2_forsale_df.pk")
df_all = app_preprocess_df(df_all)
df_all.query('-0.89 <price_pct < -0.05').to_csv('df_forsale.csv')

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

forsale_config_default = {"price-from": 500_000, "price-to": 3_000_000, "median-price-pct": -0.2,
                          "price-min": 500_000, "price-max": 10_000_000,
                          "switch-median": True,
                          "discount-price-pct": None,
                          "ai_pct": None,
                          "price_step": 50_000,
                          "price_mul": 1,  # 1e6,
                          "with_nadlan": True
                          }

app.layout = get_layout(forsale_config_default)
add_callbacks(app, df_all, forsale_config_default)

# https://python.plainenglish.io/how-to-create-a-model-window-in-dash-4ab1c8e234d3


if __name__ == '__main__':
    app.run_server(debug=True, port=8049)
