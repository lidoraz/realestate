import dash_bootstrap_components as dbc
from dash import dcc
from dash.dash_table import DataTable, FormatTemplate
import dash_leaflet as dl
from dash import html
from app_map.marker import POINT_TO_LAYER_FUN

date_added_txt = 'הועלה עד'
date_updated_text = 'עודכן לפני'
n_rooms_txt = 'חדרים'
n_floor_txt = "קומה"
median_price_txt = '% מהממוצע'
ai_pct_txt = '% ממחיר AI'
price_pct_txt = '% הורדה במחיר'
rooms_marks = {r: str(r) for r in range(7)}
rooms_marks[6] = '6+'
max_floor = 32
floor_marks = {k: str(k) for k in range(0, max_floor + 1, 4)}
floor_marks.update({0: "קרקע", 32: "32+"})
slider_tooltip = {'always_visible': True, 'placement': 'bottom'}
CLUSTER_MAX_ZOOM = 15

asset_status_cols = [
                        'חדש מקבלן (לא גרו בנכס)',
                        'חדש (גרו בנכס)',
                        'משופץ',
                        'במצב שמור',
                        'דרוש שיפוץ'][::-1]
asset_type_cols = ['דירה', 'יחידת דיור', 'דירת גן', 'סאבלט', 'דו משפחתי', 'מרתף/פרטר', 'גג/פנטהאוז', "בית פרטי/קוטג'",
                   'סטודיו/לופט', 'דופלקס', 'דירת נופש', 'משק חקלאי/נחלה', 'טריפלקס', 'החלפת דירות']

marker_type_options = [
    {'label': 'M', 'value': 'pct_diff_median', 'label_id': 'pct_diff_median'},
    {'label': '%', 'value': 'price_pct', 'label_id': 'price_pct'},
    {'label': 'AI', 'value': 'ai_price_pct', 'label_id': 'ai_price_pct'},
]
tooltips = [dbc.Tooltip("הצג לפי ממוצע המחיר של נכסים עם אותו מספר חדרים באיזור", target="pct_diff_median"),
            dbc.Tooltip("הצג את השינוי במחיר הנכס מרגע העלאה עד היום", target="price_pct"),
            dbc.Tooltip("הצג את המחיר לעומת חיזוי של בינה מלאכותית AI🚀 ", target="ai_price_pct")]
marker_type_default = 'ai_price_pct'
btn_size = 'md'
btn_color = 'primary'


# https://stackoverflow.com/questions/34775308/leaflet-how-to-add-a-text-label-to-a-custom-marker-icon
# https://community.plotly.com/t/dash-leaflet-custom-icon-for-each-marker-on-data-from-geojson/54158/10
# Can use text instead of just icon with using DivIcon in JS.

def get_page_menu():
    return dbc.DropdownMenu([dbc.DropdownMenuItem("Rent", href="/rent", external_link=True),
                             dbc.DropdownMenuItem("Sale", href="/sale", external_link=True),
                             dbc.DropdownMenuItem("Analytics", href="/analytics", external_link=True)],
                            label="§עוד", color=btn_color, size=btn_size)  # style=dict(direction="ltr")


def get_layout(default_config):
    layout = html.Div(children=[
        html.Header(className="top-container", children=get_div_top_bar(default_config)),
        # html.Span("", id="fetched-assets"),
        html.Div(className="grid-container", children=get_main_map()),
        html.Div(className="table-container", children=[div_left_off_canvas]),
        html.Div(className="modal-container", children=[div_offcanvas]),
    ])
    return layout


def get_table_container():
    return html.Div(className="left-container", children=[
        dbc.Button("Clear Marker", id="clear-cell-button", color="secondary", size='sm'),
        DataTable(
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
            hidden_columns=["id"],
            style_cell={
                # 'overflow': 'hidden',
                'font-family': 'sans-serif',
                'font-size': '11pt',
                'textOverflow': 'ellipsis',
                'minWidth': '30px', 'width': '30px', 'maxWidth': '120px',
                # 'maxWidth': 0
            },
            style_data_conditional=None  # cond_styles
        )])


def get_html_range_range_pct(text, element_id, checked=False):
    value = [] if not checked else ["Y"]
    check_mark = dcc.Checklist(options=[{'value': 'Y', 'label': text}], value=value, inline=True,
                               inputClassName="rounded-checkbox",
                               className="text-rtl",
                               id=f'{element_id}-check')
    return html.Div([check_mark,
                     dcc.RangeSlider(min=-100,
                                     max=100,
                                     step=5, value=[-100, 0],
                                     id=element_id,
                                     disabled=not checked,
                                     marks={-100: '-100%', 0: '0%', 100: '+100%'},
                                     allowCross=False,
                                     tooltip=slider_tooltip)],
                    className="slider-container-drop")


def get_div_top_bar(config_defaults):
    div_top_bar = html.Div(className="top-toolbar", children=[
        dbc.DropdownMenu([
            html.Div([
                dbc.Row(dbc.Label(id="fetched-assets")),
                html.Div([dbc.Label("עיר"),
                          dbc.Row([
                              dbc.Col(dbc.Button("X", id="search-clear", color="secondary",
                                                 style=dict(margin=0, padding=0)), width=1),
                              dbc.Col(dbc.Input(id="search-input", value="", debounce=True, type="text",
                                                placeholder="חיפוש לפי עיר", style=dict(width="89.5%")), width=11),
                          ], style={"flex-wrap": "inherit"})
                          ],
                         className="slider-container-drop"),

                html.Div([config_defaults['price_label'], dcc.RangeSlider(min=config_defaults["price-min"],
                                                      max=config_defaults["price-max"],
                                                      step=config_defaults['price_step'],
                                                      value=[config_defaults['price-from'],
                                                             config_defaults['price-to']],
                                                      id='price-slider',
                                                      marks={config_defaults["price-max"]: '+',
                                                             config_defaults["price-min"]: '-'},
                                                      allowCross=False,
                                                      tooltip=slider_tooltip)],
                         className="slider-container-drop"),
                dbc.DropdownMenuItem(divider=True),
                html.Div(
                    [html.Div([html.Span(n_rooms_txt),
                               html.Div(dcc.RangeSlider(1, 6, 1, value=[3, 4], marks=rooms_marks, id='rooms-slider',
                                                        tooltip=slider_tooltip))],
                              className='slider-container-drop'),
                     html.Div([html.Span(n_floor_txt),
                               html.Div(dcc.RangeSlider(0, max_floor, 4, value=[0, max_floor],
                                                        marks=floor_marks, id='floor-slider',
                                                        tooltip=slider_tooltip,
                                                        ))],
                              className='slider-container-drop'),
                     dcc.Dropdown(
                         asset_status_cols,
                         [],
                         placeholder="מצב הנכס",
                         multi=True,
                         searchable=False,
                         id='asset-status',
                         className="asset-dropdown"),
                     dcc.Dropdown(
                         asset_type_cols,
                         [],
                         placeholder="סוג",
                         multi=True,
                         searchable=False,
                         id='asset-type',
                         className="asset-dropdown"),
                     ], className=""),
                html.Div([dcc.Checklist(options=[{'label': 'עם תיווך', 'value': 'Y'}], value=['Y'], inline=True,
                                        inputClassName="rounded-checkbox",
                                        id='agency-check'),
                          dcc.Checklist(options=[{'label': 'חניה', 'value': 'Y'}], value=[], inline=True,
                                        inputClassName="rounded-checkbox",
                                        id='parking-check'),
                          dcc.Checklist(options=[{'label': 'מרפסת', 'value': 'Y'}], value=[], inline=True,
                                        inputClassName="rounded-checkbox",
                                        id='balconies-check')], className="dash-options"),
                dbc.DropdownMenuItem(divider=True),
                html.Div([
                    "תצוגה לפי",
                    dbc.RadioItems(
                        options=marker_type_options,
                        value=marker_type_default,
                        id='marker-type',
                        inline=True,
                    ),
                    *tooltips
                ], style={"margin-bottom": "10px"}),
                # dbc.DropdownMenu([
                #     dbc.DropdownMenuItem("סינון לפי מחירים", header=True),
                get_html_range_range_pct(ai_pct_txt, 'ai-price-pct-slider'),
                get_html_range_range_pct(price_pct_txt, 'price-discount-pct-slider'),
                get_html_range_range_pct(median_price_txt, 'price-median-pct-slider')
                # ]
                ,
                # className="dropdown-container",
                # direction="up",
                # label="סינון לפי מחירים"),

                dbc.DropdownMenuItem(divider=True),
                html.Div([dbc.Row([dbc.Col(date_added_txt),
                                   dbc.Col(dcc.Input(
                                       id="date-added",
                                       type="number",
                                       placeholder=date_added_txt,
                                       value=300,
                                       debounce=True,
                                       className="input-ltr"))]),
                          dbc.Row([dbc.Col(date_updated_text),
                                   dbc.Col(dcc.Input(
                                       id="date-updated",
                                       type="number",
                                       placeholder=date_updated_text,
                                       value=14,
                                       debounce=True,
                                       className="input-ltr"
                                   ))]),
                          dbc.Row(dcc.Checklist(options=[{'value': 'Y', 'label': "Cluster"}], value=['Y'], inline=True,
                                                inputClassName="rounded-checkbox",
                                                id='cluster-check'))], className="text-rtl"),
                dbc.Button("נקה", id="button-clear", color="secondary"),
                dbc.Row(dbc.Label("Made with ❤️"))
            ],
                className="dropdown-container")], label='אפשרויות', color=btn_color, size=btn_size),  # align_end=True,
        dbc.Button("טבלה", id="table-toggle", color=btn_color, size=btn_size),
        dbc.Button("איזור", id="button-around", color=btn_color, size=btn_size),
        # dbc.Button("סנן", id='button-return'),
        get_page_menu(),
        html.H2(config_defaults['name'].capitalize(), style={"margin": "5px 5px 0px 5px"}),
    ])
    return div_top_bar


# Leaflet-style URL
# https://leaflet-extras.github.io/leaflet-providers/preview/
# more Here:
# https://github.com/geopandas/xyzservices/blob/main/provider_sources/leaflet-providers-parsed.json
url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
url_bright = "https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png"
url_dark = "https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png"


def get_main_map():
    return dl.Map(children=[dl.TileLayer(url=url_bright),
                            dl.GeoJSON(data=None, id="geojson", zoomToBounds=False, cluster=False,
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
    title=False,
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
                          precision=2,
                          group=Group.yes,
                          groups=3,
                          group_delimiter=',',
                          decimal_delimiter='.',
                          symbol=Symbol.yes,
                          symbol_prefix=u'₪')
    columns_output_comb = {"price": dict(id='price', name='Price', type='numeric', format=price_format),
                           "rooms": dict(id='rooms', name='R', type='numeric'),
                           # "parking": dict(id='parking', name='Parking', type='numeric'),
                           pct_cols[2]: dict(id=pct_cols[2], name='AI', type='numeric',
                                             format=FormatTemplate.percentage(0)),
                           pct_cols[1]: dict(id=pct_cols[1], name='#M', type='numeric',
                                             format=FormatTemplate.percentage(0)),
                           pct_cols[0]: dict(id=pct_cols[0], name='%D', type='numeric',
                                             format=FormatTemplate.percentage(0)),
                           'square_meters': dict(id='square_meters', name='Sq', type='numeric'),
                           "avg_price_m": dict(id='avg_price_m', name='AvgSq₪', type='numeric', format=price_format),
                           "id": dict(id="id", name='id'),
                           "city": dict(id='city', name='city')}
    cond_styles, legend = _discrete_background_color_bins(df, columns=pct_cols, reverse=True)
    columns = list(columns_output_comb.values())
    data = df[columns_output_comb.keys()].to_dict('records')
    style_data_conditional = cond_styles
    return columns, data, style_data_conditional
