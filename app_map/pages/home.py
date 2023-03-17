import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

from app_map.util_layout import get_page_menu

dash.register_page(__name__, path='/', external_stylesheets=[dbc.themes.BOOTSTRAP])

layout = html.Div(children=[
    html.H1(children='Real estate'),
    get_page_menu(),
    html.Div(children='''Click on menu'''),

])
