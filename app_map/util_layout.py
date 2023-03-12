import dash_bootstrap_components as dbc
from dash import dcc
from dash.dash_table import DataTable, FormatTemplate
import dash_leaflet as dl
from dash import html
from app_map.marker import POINT_TO_LAYER_FUN

price_text = "מחיר"
date_added_txt = 'הועלה עד'
date_updated_text = 'עודכן לפני'
n_rooms_txt = 'חדרים'
median_price_txt = '% מהחציון'
ai_pct_txt = '% ממחירAI '
price_pct_txt = '% שינוי מחיר'
rooms_marks = {r: str(r) for r in range(7)}
rooms_marks[6] = '6+'

CLUSTER_MAX_ZOOM = 15


# https://stackoverflow.com/questions/34775308/leaflet-how-to-add-a-text-label-to-a-custom-marker-icon
# https://community.plotly.com/t/dash-leaflet-custom-icon-for-each-marker-on-data-from-geojson/54158/10
# Can use text instead of just icon with using DivIcon in JS.

def get_layout(default_config):
    layout = html.Div(children=[
        html.Div(className="top-container", children=get_div_top_bar(default_config)),
        html.Div(className="grid-container", children=get_main_map()),
        html.Div(className="table-container", children=[div_left_off_canvas]),
        html.Div(className="modal-container", children=[div_offcanvas]),
        dcc.Interval(
            id='interval-component',
            interval=1* 1000,  # in milliseconds
            n_intervals=0
        )
    ])
    return layout


def get_table_container():
    return html.Div(className="left-container", children=[DataTable(
        id='datatable-interactivity',
        columns=None,
        data=None,
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
        page_size=15,
        # hidden_columns=["id"],
        style_cell={
            # 'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'minWidth': '30px', 'width': '180px', 'maxWidth': '180px',
            # 'maxWidth': 0
        },

        style_data_conditional=None  # cond_styles
    )])


def get_html_range_range_pct(text, element_id):
    check_mark = dbc.Checklist(options=[{'value': 'Y', 'label': text}], value=['Y'], inline=True,
                               inputClassName="rounded-checkbox",
                               id=f'{element_id}-check')
    return html.Div([check_mark,
                     dcc.RangeSlider(min=-100,
                                     max=100,
                                     step=5, value=[-100, 0],
                                     id=element_id,
                                     marks={-100: '-100%', 0: '0%', 100: '+100%'},
                                     allowCross=False,
                                     tooltip={'always_visible': True, 'placement': 'bottom'})],
                    className="slider-container")


def get_div_top_bar(config_defaults):
    div_top_bar = html.Div(className="top-toolbar", children=[
        # dbc.Button("RE"),
        # TODO: ADD SWITCH FOR ADDING AI_PCT as a dropdown.
        dbc.RadioItems(
            options=[
                {'label': 'M', 'value': 'pct_diff_median'},
                {'label': '%', 'value': 'price_pct'},
                {'label': 'AI', 'value': 'ai_price_pct'},
            ],
            value='pct_diff_median',
            id='marker-type'
        ),
        # dcc.Slider(0, 2, 1, value=1, marks={0: 'a', 1: 'b', 2: 'c'}, id='marker-type1'),
        # html.Span(from_price_txt),
        html.Div([html.Span(price_text), dcc.RangeSlider(min=config_defaults["price-min"],
                                                         max=config_defaults["price-max"],
                                                         step=config_defaults['price_step'],
                                                         value=[config_defaults['price-from'],
                                                                config_defaults['price-to']],
                                                         id='price-slider', marks={config_defaults["price-max"]: '+',
                                                                                   config_defaults["price-min"]: '-'},
                                                         allowCross=False,
                                                         tooltip={'always_visible': True})],
                 className="slider-container"),
        get_html_range_range_pct(median_price_txt, 'price-median-pct-slider'),
        get_html_range_range_pct(price_pct_txt, 'price-discount-pct-slider'),
        get_html_range_range_pct(ai_pct_txt, 'ai-price-pct-slider'),
        dcc.Checklist(options=[{'label': 'תיווך', 'value': 'Y'}], value=['Y'], inline=True,
                      inputClassName="rounded-checkbox",
                      id='agency-check'),
        dcc.Checklist(options=[{'label': 'חניה', 'value': 'Y'}], value=[], inline=True,
                      inputClassName="rounded-checkbox",
                      id='parking-check'),
        dcc.Checklist(options=[{'label': 'מרפסת', 'value': 'Y'}], value=[], inline=True,
                      inputClassName="rounded-checkbox",
                      id='balconies-check'),
        html.Div(dcc.RangeSlider(1, 6, 1, value=[3, 4], marks=rooms_marks, id='rooms-slider'),
                 style={"min-width": "10em"}),
        dcc.Dropdown(
            ['משופץ', 'במצב שמור', 'חדש (גרו בנכס)', 'חדש מקבלן (לא גרו בנכס)', 'דרוש שיפוץ'],
            [],
            placeholder="מצב הנכס",
            multi=True,
            searchable=False,
            id='state-asset',
            style=dict(width='10em', )),
        html.Span(date_added_txt),
        dcc.Input(
            id="date-added",
            type="number",
            placeholder=date_added_txt,
            value=360,
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
        # dbc.Switch(value=config_defaults["switch-median"], id='switch-median'),
        # dbc.Button(children="AAAAAA"),
        dbc.Button("איזור", id="button-around"),
        dbc.Button("סנן", id='button-return'),
        dbc.Button(children="נקה", id="button-clear"),
        dbc.Button(html.Span("0", id="fetched-assets"), color="secondary"),
        dbc.Button("TBL", id="table-toggle", color="success"),
    ])
    return div_top_bar


# Leaflet-style URL
# https://leaflet-extras.github.io/leaflet-providers/preview/
# more Here:
# https://github.com/geopandas/xyzservices/blob/main/provider_sources/leaflet-providers-parsed.json

def get_main_map():
    return dl.Map(children=[dl.TileLayer(url="https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png"),
                            dl.GeoJSON(data=None, id="geojson", zoomToBounds=False, cluster=True,
                                       superClusterOptions=dict(maxZoom=CLUSTER_MAX_ZOOM),  # radius=50,
                                       options=dict(pointToLayer=POINT_TO_LAYER_FUN),
                                       ),
                            dl.Marker(position=[31.7, 32.7], opacity=0, id='map-marker')
                            ],
                  zoom=3, id='big-map', zoomControl=True,
                  bounds=[[31.7, 32.7], [32.5, 37.3]]
                  )


div_left_off_canvas = dbc.Offcanvas(
    get_table_container(),
    id="table-modal",
    scrollable=True,
    title="Scrollable Offcanvas",
    backdrop=False,
    is_open=False
)

div_offcanvas = html.Div([dbc.Offcanvas(
    children=[dbc.ModalTitle(id="modal-title"), html.Div(id='country'), html.Div(id='marker'),
              dcc.Graph(id='histogram', figure={},
                        config={'displayModeBar': False,
                                'scrollZoom': False}),
              html.Div(id='Country info pane')],
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


def get_interactive_table(df):
    table_price_col = 'ai_price_pct'
    pct_cols = ['price_pct',
                'pct_diff_median',
                'ai_price_pct']
    from dash.dash_table.Format import Format, Symbol, Group, Scheme
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
    columns_output_comb = {"price": dict(id='price', name='Price', type='numeric', format=price_format),
                           "rooms": dict(id='rooms', name='R', type='numeric'),
                           # "parking": dict(id='parking', name='Parking', type='numeric'),
                           pct_cols[0]: dict(id=pct_cols[0], name='%D', type='numeric',
                                             format=FormatTemplate.percentage(0)),
                           pct_cols[2]: dict(id=pct_cols[2], name='AI', type='numeric',
                                             format=FormatTemplate.percentage(0)),
                           pct_cols[1]: dict(id=pct_cols[1], name='#M', type='numeric',
                                             format=FormatTemplate.percentage(0)),
                           # "avg_price_m": dict(id='price', name='Price', type='numeric', format=price_format),
                           "id": dict(id="id", name='id'),
                           "city": dict(id='city', name='city')}
    cond_styles, legend = _discrete_background_color_bins(df, columns=pct_cols, reverse=True)
    columns = list(columns_output_comb.values())
    data = df[columns_output_comb.keys()].to_dict('records')
    style_data_conditional = cond_styles
    return columns, data, style_data_conditional
