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

from app_map.marker import POINT_TO_LAYER_FUN
# from app_map.utils import *

from_price_txt = 'ממחיר'
to_price_txt = 'עד מחיר'
date_added_txt = 'הועלה עד '
date_updated_text = 'עודכן לפני'
n_rooms_txt = 'מספר חדרים'
median_price_txt = '% מהחציון'
ai_pct_txt = '% ממחירAI '
price_pct_txt = 'שינוי במחיר'
rooms_marks = {r: str(r) for r in range(7)}
rooms_marks[6] = '6+'

# https://stackoverflow.com/questions/34775308/leaflet-how-to-add-a-text-label-to-a-custom-marker-icon
# https://community.plotly.com/t/dash-leaflet-custom-icon-for-each-marker-on-data-from-geojson/54158/10
# Can use text instead of just icon with using DivIcon in JS.


def get_div_top_bar(config_defaults):
    div_top_bar = html.Div(className="top-toolbar", children=[
        dbc.Button(children=[html.Span('סה"כ:'), html.Span("0", id="fetched-assets")]),
        html.Span(from_price_txt),
        dcc.Input(
            id="price-from",
            type="number",
            placeholder=from_price_txt,
            value=config_defaults["price-from"],
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
            value=config_defaults["price-to"],
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
            value=config_defaults["median-price-pct"],
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
            value=config_defaults["discount-price-pct"],
            debounce=True,
            step=0.01,
            min=-1,
            max=1,
            className="input-ltr"
        ),
        html.Span(ai_pct_txt),
        dcc.Input(
            id="ai_pct",
            type="number",
            placeholder=ai_pct_txt,
            value=config_defaults["ai_pct"],
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
        # TODO: ADD SWITCH FOR ADDING AI_PCT as a dropdown.
        dbc.Switch(value=config_defaults["switch-median"], id='switch-median'),
        # dbc.Button(children="AAAAAA"),
        dbc.Button("איזור", id="button-around"),
        dbc.Button("סנן", id='button-return'),

        dbc.Button(children="נקה", id="button-clear"),
        # html.Span(n_rooms_txt),
        html.Div(dcc.RangeSlider(1, 6, 1, value=[3, 4], marks=rooms_marks, id='rooms-slider'),
                 style={"min-width": "10em"}),
    ])
    return div_top_bar


div_left_map = html.Div(className="left-div", children=[
    dl.Map(children=[dl.TileLayer(),
                     dl.GeoJSON(data=None, id="geojson", zoomToBounds=False, cluster=True,
                                # superClusterOptions=dict(radius=50, maxZoom=12),
                                options=dict(pointToLayer=POINT_TO_LAYER_FUN),
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


def _discrete_background_color_bins(df, n_bins=10, columns='all', reverse=False):
    import colorlover
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if columns == 'all':
        if 'id' in df:
            df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
        else:
            df_numeric_columns = df.select_dtypes('number')
    else:
        df_numeric_columns = df[columns]
    df_max = 0.2  # df_numeric_columns.max().max()
    df_min = -0.2  # df_numeric_columns.min().min()
    ranges = [((df_max - df_min) * i) + df_min for i in bounds]
    ranges[0] = -1
    ranges[-1] = 1
    styles = []
    legend = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        bg_color = colorlover.scales[str(n_bins)]['div']['RdYlGn']
        if reverse:
            bg_color = bg_color[::-1]
        bg_color = bg_color[i - 1]
        color = 'white' if i == 1 or i == len(bounds) - 1 else 'inherit'

        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                            '{{{column}}} >= {min_bound}' +
                            (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': bg_color,
                'color': color
            })
        legend.append(
            html.Div(style={'display': 'inline-block', 'width': '35px'}, children=[
                html.Div(
                    style={
                        'backgroundColor': bg_color,
                        'borderLeft': '1px rgb(50, 50, 50) solid',
                        'height': '10px'
                    }
                ),
                html.Small(f'{round(min_bound * 100)}%', style={'paddingLeft': '2px'}) if i > 1 else html.Small('%:')
            ])
        )
    return styles, html.Div(legend, style={'padding': '5px 0 5px 0'})


def get_table(df):
    table_price_col = 'ai_price_pct'
    columns = ['last_price', 'rooms', table_price_col, 'city']  # price_pct
    from dash.dash_table.Format import Format, Symbol, Group, Scheme
    df = df[columns]
    money = FormatTemplate.money(2)
    percentage = FormatTemplate.percentage(2)
    # Format().symbol(Symbol.yes).symbol_prefix('₪ ')._specifier(',.0f')d
    price_format = Format(scheme=Scheme.decimal_si_prefix,
                          precision=3,
                          group=Group.yes,
                          groups=3,
                          group_delimiter=',',
                          decimal_delimiter='.',
                          symbol=Symbol.yes,
                          symbol_prefix=u'₪ ')
    columns_output = [
        dict(id='last_price', name='Price', type='numeric', format=price_format),  # , locale=dict(symbol=['₪ ', ''])
        dict(id='rooms', name='R', type='numeric'),
        dict(id=table_price_col, name='% AI', type='numeric', format=FormatTemplate.percentage(0)),
        # dict(id='price_pct', name='% Chg', type='numeric', format=percentage),
        dict(id='city', name='city'),
    ]
    cond_styles, legend = _discrete_background_color_bins(df, columns=[table_price_col], reverse=True)
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
        row_selectable=False,  # 'single',  # "multi",
        row_deletable=False,
        # active_cell=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current=0,
        page_size=20,
        style_cell={
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0
        },
        style_data_conditional=cond_styles
    )
    return [tbl]
