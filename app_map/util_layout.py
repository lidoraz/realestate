import time
import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash.dash_table import DataTable, FormatTemplate
import dash_leaflet as dl
from plotly import graph_objects as go
from dash import html, Output, Input, State, ctx
import numpy as np
from datetime import datetime
import pandas as pd

from app_map.utils import *

from_price_txt = 'ממחיר(א)'
to_price_txt = 'עד מחיר(א)'
date_added_txt = 'הועלה עד '
date_updated_text = 'עודכן לפני'
n_rooms_txt = 'מספר חדרים'
median_price_txt = '% מהחציון'
price_pct_txt = 'שינוי במחיר'
rooms_marks = {r: str(r) for r in range(7)}
rooms_marks[6] = '6+'

div_top_bar = html.Div(className="top-toolbar", children=[
    dbc.Button(children=[html.Span('סה"כ:'), html.Span("0", id="fetched-assets")]),
    html.Span(from_price_txt),
    dcc.Input(
        id="price-from",
        type="number",
        placeholder=from_price_txt,
        value=0.5,
        step=0.1,
        min=0,
        debounce=True,
        className='input-ltr'
    ),
    html.Span(to_price_txt),
    dcc.Input(
        id="price-to",
        type="number",
        placeholder=to_price_txt,
        value=3,
        step=0.1,
        min=0,
        debounce=True,
        className='input-ltr'
    ),
    html.Span(median_price_txt),
    dcc.Input(
        id="median-price-pct",
        type="number",
        placeholder=median_price_txt,
        value=-0.2,
        debounce=True,
        step=0.01,
        min=-1,
        max=1,
        className="input-ltr"
    ),
    html.Span(price_pct_txt),
    dcc.Input(
        id="discount-price-pct",
        type="number",
        placeholder=price_pct_txt,
        value=None,
        debounce=True,
        step=0.01,
        min=-1,
        max=1,
        className="input-ltr"
    ),
    html.Span(date_added_txt),
    dcc.Input(
        id="date-added",
        type="number",
        placeholder=date_added_txt,
        value=100,
        debounce=True,
        className="input-ltr"
    ),
    html.Span(date_updated_text),
    dcc.Input(
        id="date-updated",
        type="number",
        placeholder=date_updated_text,
        value=30,
        debounce=True,
        className="input-ltr"
    ),
    dcc.Checklist(options=[{'label': 'כולל תיווך', 'value': 'Y'}], value=['Y'], inline=True,
                  id='agency-check'),
    dcc.Checklist(options=[{'label': 'חובה חניה', 'value': 'Y'}], value=[], inline=True,
                  id='parking-check'),
    dcc.Checklist(options=[{'label': 'חובה מרפסת', 'value': 'Y'}], value=[], inline=True,
                  id='balconies-check'),
    dcc.Dropdown(
        ['משופץ', 'במצב שמור', 'חדש (גרו בנכס)', 'חדש מקבלן (לא גרו בנכס)', 'דרוש שיפוץ'],
        [],
        placeholder="מצב הנכס",
        multi=True,
        searchable=False,
        id='state-asset',
        style=dict(width='10em', )),
    html.Span('שיטה'),
    dbc.Switch(value=True, id='switch-median'),
    # dbc.Button(children="AAAAAA"),
    dbc.Button("באיזור", id="button-around"),
    dbc.Button("סנן", id='button-return'),

    dbc.Button(children="נקה", id="button-clear"),
    html.Span(n_rooms_txt),
    html.Div(dcc.RangeSlider(1, 6, 1, value=[3, 4], marks=rooms_marks, id='rooms-slider'),
             style=dict(width="30em")),
])
div_left_map = html.Div(className="left-div", children=[
    dl.Map(children=[dl.TileLayer(),
                     dl.GeoJSON(data=None, id="geojson", zoomToBounds=False, cluster=True,
                                # superClusterOptions=dict(radius=50, maxZoom=12),
                                options=dict(pointToLayer=js_draw_icon_div),
                                ),
                     ],
           zoom=3, id='map', zoomControl=True,
           bounds=[[31.7, 32.7], [32.5, 37.3]]
           ),

])

div_offcanvas = html.Div([dbc.Offcanvas(
    [
        # dbc.ModalHeader(dbc.ModalTitle("Header")),
        dbc.ModalBody(children=[html.Div(children=[html.Div(id='country'), html.Div(id='marker'),
                                                   dcc.Graph(id='histogram', figure={},
                                                             config={'displayModeBar': False,
                                                                     'scrollZoom': False}),
                                                   html.Div(id='Country info pane')])]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close", className="ms-auto", n_clicks=0)
        ),
    ],
    id="modal",
    placement="end",
    is_open=False,
    style=dict(width="500px", direction="rtl")
)])


def get_table(df):
    columns = ['last_price', 'rooms', 'price_pct', 'city']
    from dash.dash_table.Format import Format, Symbol, Group, Scheme
    df = df[columns]
    money = FormatTemplate.money(2)
    percentage = FormatTemplate.percentage(2)
    # Format().symbol(Symbol.yes).symbol_prefix('₪ ')._specifier(',.0f')d
    price_format = Format(scheme=Scheme.fixed,
                          precision=0,
                          group=Group.yes,
                          groups=3,
                          group_delimiter=',',
                          decimal_delimiter='.',
                          symbol=Symbol.yes,
                          symbol_prefix=u'₪ ')
    columns_output = [
        dict(id='last_price', name='Price', type='numeric', format=price_format),  # , locale=dict(symbol=['₪ ', ''])
        dict(id='rooms', name='R', type='numeric'),
        dict(id='price_pct', name='% Chg', type='numeric', format=percentage),
        dict(id='city', name='city'),
    ]
    tbl = DataTable(
        id='datatable-interactivity',
        columns=columns_output,
        # columns=[
        #     {"name": i, "id": i, "deletable": False, "selectable": False} for i in df.columns
        # ],
        data=df.to_dict('records'),
        editable=False,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable="single",
        row_selectable=False,  # "multi",
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=20,
    )
    return [tbl]
