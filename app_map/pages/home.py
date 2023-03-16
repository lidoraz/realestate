import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
dash.register_page(__name__, path='/',  external_stylesheets=[dbc.themes.BOOTSTRAP])

layout = html.Div(children=[
    html.H1(children='This is our Home page'),

    html.Div(children='''
        This is our Home page content.
    '''),

])