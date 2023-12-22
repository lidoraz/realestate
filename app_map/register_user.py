import dash
from dash import html, Output, Input, State, dcc
from ext.db_user import insert_or_update_user
from ext.crypto import decrypt
import dash_bootstrap_components as dbc
from datetime import datetime
import urllib.parse
import os

from ext.env import get_pg_engine

# TODO: fail the page loadout if the id decrypt failed to generate valid number
# get_pg_engine(echo=False, use_vault=False)  # just to load all the env and sanity-check
BASE_URL = "register_"

width = 10


def get_asset_options_html(asset_type):
    assert asset_type in ("rent", "sale")
    # Default values for rent and sale options
    default_price_from, default_price_to = (3000, 7000) if asset_type == "rent" else (1_000_000, 3_000_000)
    sale_min_price = 100_000
    sale_max_price = 5000000
    rent_min_price = 1000
    rent_max_price = 10_000
    sale_price_marks = {sale_min_price: '100k', 1_000_000: '1M', 2000000: '2M', 3000000: '3M', 4000000: '4M',
                        sale_max_price: '5M+'}
    rent_price_marks = {rent_min_price: '1K', 2000: '2K', 4000: '4K', 6000: '6K', 8000: '8K',
                        rent_max_price: '10K+'}
    rooms_marks = {i: f'{i}' for i in range(7)}
    rooms_marks[6] = '6+'
    step = 500 if asset_type == "rent" else 50_000

    min_price = rent_min_price if asset_type == "rent" else sale_min_price
    max_price = rent_max_price if asset_type == "rent" else sale_max_price
    price_marks = rent_price_marks if asset_type == "rent" else sale_price_marks
    default_rooms_from, default_rooms_to = (3, 4)  # Default number of rooms
    rangeslider_tooltip = {'always_visible': True, 'placement': 'top'}

    return [
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Label("Relevant cities"),
                            dcc.Dropdown(
                                id=f"input-{asset_type}-cities",
                                options=[{"label": option, "value": option} for option in
                                         cities],
                                multi=True,
                                placeholder="Select cities...",
                            ),
                        ]
                    ),
                    width=width,
                ),
            ]
            , justify="center"),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Label("Price Range ₪"),
                            dcc.RangeSlider(
                                id=f"input-{asset_type}-price-range",
                                marks=price_marks,
                                step=step,
                                min=min_price, max=max_price,
                                tooltip=rangeslider_tooltip,
                                value=[default_price_from, default_price_to],
                            ),
                        ]
                    ),
                    width=width,
                ),
            ]
            , justify="center"),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Label("Number of Rooms"),
                            dcc.RangeSlider(
                                id=f"input-{asset_type}-rooms-range",
                                step=1.0,
                                marks=rooms_marks,
                                min=1, max=6,
                                tooltip=rangeslider_tooltip,
                                value=[default_rooms_from, default_rooms_to],
                            ),
                        ]
                    ),
                    width=width,
                ),
            ]
            , justify="center"),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Label("Asset Condition"),
                            dcc.Dropdown(
                                id=f"input-{asset_type}-asset-cond",
                                options=[{"label": option, "value": option} for option in
                                         asset_condition_options],
                                multi=True,
                                placeholder="Select asset condition",
                            ),
                        ]
                    ),
                    width=width,
                ),
            ]
            , justify="center"),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Label("Is Balcony, Parking a must have?\n What about agency?", className="mt-3 mb-2"),
                            dcc.Checklist(
                                ['Parking', 'Balcony', 'No Agency'],
                                [],
                                inputStyle={"margin-left": "20px", "margin-right": "5px"},
                                id=f"input-{asset_type}-more-options",
                                inline=True
                            ),
                        ]
                    ),
                    width=width,
                ),
            ]
            , justify="center"),
    ]


def create_asset_preferences(price_from, price_to, rooms_from,
                             rooms_to, asset_cond, cities,
                             must_parking, must_balcony, must_no_agency):
    asset_preferences = {
        "min_price": price_from,
        "max_price": price_to,
        "min_rooms": rooms_from,
        "max_rooms": rooms_to,
        "asset_status": [] if asset_cond is None else asset_cond,
        "cities": cities,
        "must_parking": must_parking,
        "must_balcony": must_balcony,
        "must_no_agency": must_no_agency,
    }
    return asset_preferences


def get_dash(server):
    assert os.getenv("TELEGRAM_USERID_SALT")  # used for crypto
    app = dash.Dash(server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], title="Register",
                    url_base_pathname=f'/{BASE_URL}/')

    app.layout = dbc.Container(
        [
            dcc.Location(id='url', refresh=False),  # Ad
            dbc.Row(
                dbc.Col(html.H1("Agent App, Rent & Sale", className="text-center mb-4"), width=12),
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Form(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Row(
                                            [
                                                dbc.Label("Name", className="font-weight-bold"),
                                                dbc.Input(id="input-name", type="text", placeholder="Enter your name"),
                                            ]
                                        ),
                                        width=width,
                                    ),
                                ]
                                , justify="center"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Row(
                                            [
                                                dbc.Label("Telegram ID", className="font-weight-bold"),
                                                dbc.Input(id="input-telegram-id", type="text", disabled=True,
                                                          placeholder="Enter your Telegram ID"),
                                            ]
                                        ),
                                        width=width,
                                    ),
                                ]
                                , justify="center"),
                            html.Hr(),
                            dbc.Row(html.H3(rent_header_closed,
                                            className="mt-4 mb-3",
                                            n_clicks=0,
                                            id="rent-options-header"),
                                    justify="center"),

                            dbc.Collapse(
                                get_asset_options_html("rent"),
                                id="rent-options-collapse",
                                className="collapse-cont",
                                is_open=False
                            ),

                            html.Hr(),

                            dbc.Row(html.H3(sale_header_closed,
                                            className="mt-4 mb-3",
                                            n_clicks=0,
                                            id="sale-options-header"),
                                    justify="center"),
                            dbc.Collapse(
                                get_asset_options_html("sale"),
                                id="sale-options-collapse",
                                className="collapse-cont",
                                is_open=False
                            ),
                            html.Hr(),
                            dbc.Alert(
                                None,
                                id='submit-alert',
                                color='danger',
                                is_open=False,
                                duration=15_000,
                            ),

                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Button("Submit", id="btn-submit", color="primary"),
                                        width={"size": width},  # Center the button
                                    ),
                                ]
                                , justify="center", class_name="register-submit-row text-center"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(id="output-json", className="mt-3 text-center"),  # Center the output
                                        width=12,
                                    ),
                                ]
                                , justify="center"),
                        ]
                    ),
                ),
            ),
        ],
        className="register-container noselect",
        fluid=True,  # Set fluid to True for a full-width container
    )

    def extract_range_values(range_values):
        return range_values[0], range_values[1]

    def process_more_options(more_options):
        must_balcony = 'Balcony' in more_options
        must_parking = 'Parking' in more_options
        must_no_agency = 'No Agency' in more_options
        return must_balcony, must_parking, must_no_agency

    def generate_preferences(price_range, rooms_range, asset_cond, cities, more_options):
        price_from, price_to = extract_range_values(price_range)
        rooms_from, rooms_to = extract_range_values(rooms_range)
        must_balcony, must_parking, must_no_agency = process_more_options(more_options)

        return create_asset_preferences(
            price_from, price_to, rooms_from, rooms_to, asset_cond, cities,
            must_parking, must_balcony, must_no_agency
        ) if price_range else None

    @app.callback(
        [
            Output("submit-alert", "is_open"),
            Output("submit-alert", "children"),
            Output("submit-alert", "color"),
        ],
        [Input("btn-submit", "n_clicks")],
        [
            State("input-name", "value"),
            State("input-telegram-id", "value"),
            State("input-rent-price-range", "value"),
            State("input-rent-rooms-range", "value"),
            State("input-rent-asset-cond", "value"),
            State("input-rent-cities", "value"),
            State("input-rent-more-options", "value"),
            State("rent-options-collapse", "is_open"),
            State("input-sale-price-range", "value"),
            State("input-sale-rooms-range", "value"),
            State("input-sale-asset-cond", "value"),
            State("input-sale-cities", "value"),
            State("input-sale-more-options", "value"),
            State("sale-options-collapse", "is_open"),
        ],
    )
    def generate_json(
            n_clicks,
            name,
            telegram_id,
            rent_price_range,
            rent_rooms_range,
            rent_asset_cond,
            rent_cities,
            rent_more_options,
            rent_is_open,
            sale_price_range,
            sale_rooms_range,
            sale_asset_cond,
            sale_cities,
            sale_more_options,
            sale_is_open,
    ):
        if not n_clicks:
            return dash.no_update

        if not (telegram_id and name) or (isinstance(telegram_id, str) and not telegram_id.isnumeric()):
            return True, alert_bad_missing_name, "danger"

        is_anything_selected = sale_is_open or rent_is_open
        if not is_anything_selected:
            return True, alert_bad_no_asset_type_selected, "danger"

        if rent_is_open and not rent_cities:
            return True, alert_bad_missing_creds_rent, "danger"

        if sale_is_open and not sale_cities:
            return True, alert_bad_missing_creds_sale, "danger"

        rent_preferences = generate_preferences(
            rent_price_range, rent_rooms_range, rent_asset_cond, rent_cities, rent_more_options
        ) if rent_is_open else None

        sale_preferences = generate_preferences(
            sale_price_range, sale_rooms_range, sale_asset_cond, sale_cities, sale_more_options
        ) if sale_is_open else None

        time_now = datetime.utcnow()
        print(f"Adding {time_now=}, {telegram_id=}, {rent_preferences=}, {sale_preferences=}")
        data = {
            "name": name,
            "telegram_id": telegram_id,
            "rent_preferences": rent_preferences,
            "sale_preferences": sale_preferences,
            "inserted_at": time_now,
            "updated_at": time_now,
        }
        res = insert_or_update_user(data)
        if res == 'insert':
            return True, alert_ok, "success"
        elif res == 'update':
            return True, alert_update, "warning"
        elif res == 'err':
            return True, alert_bad_duplicate_user, 'danger'

        return False, alert_ok, True

    @app.callback(
        [Output("input-telegram-id", "value")],
        [Input("url", "search")]
    )
    def update_url_params(search):
        # Parse URL parameters
        url_params = dict(x.split('=') for x in search[1:].split('&')) if search else {}
        print(f"{url_params=}")
        # Autofill Telegram ID
        telegram_id = url_params.get("telegram_id")
        if telegram_id:
            telegram_id = urllib.parse.unquote(telegram_id)
            print("--- >", telegram_id)
            try:
                telegram_id = decrypt(telegram_id)
                return [telegram_id]
            except ValueError as e:
                print("ValueError: Got invalid id for decrypt telegram_id")
                # from flask import Response
                # Response('Not permitted', 403)
                return dash.no_update
        else:
            return dash.no_update

    @app.callback(
        [Output("rent-options-collapse", "is_open"),
         Output("rent-options-header", "children")],
        [Input("rent-options-header", "n_clicks")],
        [State("rent-options-collapse", "is_open")]
    )
    def toggle_rent_options(n_clicks, is_open):
        if n_clicks == 0:
            return [False, rent_header_closed]
        if is_open:
            return [not is_open, rent_header_closed]
        if not is_open:
            return [not is_open, rent_header_open]

    @app.callback(
        [Output("sale-options-collapse", "is_open"),
         Output("sale-options-header", "children")],
        [Input("sale-options-header", "n_clicks")],
        [State("sale-options-collapse", "is_open")]
    )
    def toggle_sale_options(n_clicks, is_open):
        if n_clicks == 0:
            return [False, sale_header_closed]
        if is_open:
            return [not is_open, sale_header_closed]
        if not is_open:
            return [not is_open, sale_header_open]

    # @app.callback()

    return server, app


asset_condition_options = ['חדש מקבלן (לא גרו בנכס)',
                           'חדש (גרו בנכס)',
                           'משופץ',
                           'במצב שמור',
                           'דרוש שיפוץ']
cities = sorted(
    ['תל אביב יפו', 'ירושלים', 'חיפה', 'באר שבע', 'אשדוד', 'נתניה', 'ראשון לציון', 'פתח תקווה', 'רמת גן', 'אשקלון',
     'הרצליה', 'בת ים', 'רחובות', 'חולון', 'רעננה', 'נהריה', 'חדרה', 'כפר סבא', 'עפולה', 'לוד', 'הוד השרון', 'חריש',
     'קרית מוצקין', 'רמת השרון', 'קרית אתא', 'טבריה', 'רמלה', 'גבעתיים', 'בית שמש', 'מודיעין מכבים רעות', 'קרית גת',
     'קרית ביאליק', 'אילת', 'נתיבות', 'בני ברק', 'ראש העין', 'פרדס חנה כרכור', 'יבנה', 'קרית ים', 'כפר יונה', 'כרמיאל',
     'מעלה אדומים', 'אופקים', 'אור עקיבא', 'קרית אונו', 'עכו', 'דימונה', 'באר יעקב', 'מגדל העמק', 'טירת כרמל',
     'קרית מלאכי'])

rent_header_closed = "💰 Rent Options - (click to enable)"
rent_header_open = "💰 Rent Options - (click to disable)"
sale_header_closed = "🏠 Sale Options - (click to enable)"
sale_header_open = "🏠 Sale Options - (click to disable)"

alert_bad_missing_creds = "Please select at least one city."
alert_bad_missing_creds_rent = "Rent options have missing details:\n" + alert_bad_missing_creds
alert_bad_missing_creds_sale = "Sale options have missing details:\n" + alert_bad_missing_creds
alert_bad_duplicate_user = "User with that name already exists."
alert_bad_no_asset_type_selected = "Must enable one of the two options: Rent or Sale"
alert_bad_missing_name = "User name or Telegram ID are missing"
alert_ok = "Successfully submit your options!\nSoon you will receive new assets according to your preferences!"
alert_update = "Successfully updated your profile"

if __name__ == "__main__":
    os.environ["TELEGRAM_USERID_SALT"] = "test"
    _, app = get_dash(True)
    app.run_server(debug=True, port=8048)
