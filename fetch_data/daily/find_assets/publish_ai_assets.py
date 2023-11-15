import pandas as pd
from datetime import date, timedelta
import os
from ext.publish import send_to_telegram_channel
from ext.env import load_vault

config_rent = dict(min_price=4000, max_price=8000, min_rooms=3, max_rooms=4,
                   ai_price_pct_less_than=-0.07,
                   parking=True, balconies=True,  # is_agency=False,
                   asset_status=["משופץ", "חדש (גרו בנכס)", "חדש מקבלן (לא גרו בנכס)"],
                   cities=[
                       "תל אביב יפו",
                       "רמת גן",
                       "גבעתיים",
                       "הרצליה", ],
                   ai_std_pct=0.07, asset_type="rent")
config_sale = dict(min_price=1_000_000, max_price=3_000_000, min_rooms=3, max_rooms=4,
                   ai_price_pct_less_than=-0.12,
                   cities=[
                       "תל אביב יפו",
                       "ראשון לציון",
                       "רמת גן",
                       "אור יהודה",
                       "גבעתיים",
                       "הרצליה", ],
                   ai_std_pct=0.07, asset_type="forsale")

load_vault()
bot_id = os.getenv('TELEGRAM_BOT_ID') or os.getenv("TELEGRAM_TOKEN")
group_id = os.getenv('TELEGRAM_REALESTATE_DEALS_CHANNEL')
assert bot_id
assert group_id


def filter_assets(c, days_back=1):
    df = pd.read_pickle(f"resources/yad2_{c['asset_type']}_df.pk")
    yesterday = pd.to_datetime(date.today()) - timedelta(days=days_back)
    assert pd.to_datetime(df['processing_date'].max()) >= yesterday
    print(f"Starting with {len(df):,.0f} assets with asset_type={c['asset_type']}")
    df = df[df['city'].isin(c['cities'])]
    print(df['city'].value_counts().to_dict())
    if c.get('balconies'):
        df = df[df['balconies']]
    if c.get('parking'):
        df = df[df['parking'] > 0]
    if c.get('is_agency'):
        df = df[df['is_agency']]
    if c.get('asset_status'):
        df = df[df['asset_status'].isin(c['asset_status'])]
    print(len(df))
    df = df[pd.to_datetime(df['date_added']) >= yesterday]
    df = df[df['price'].between(c['min_price'], c['max_price'])]
    df = df[df['rooms'].between(c['min_rooms'], c['max_rooms'])]
    print(len(df))
    df = df[df['ai_std_pct'] < c['ai_std_pct']]
    df['pct'] = df['price'] / df['ai_price'] - 1
    df = df[df['pct'] < c['ai_price_pct_less_than']]
    df = df.sort_values('pct')
    # use square meters built, if 0 take square meters
    df['square_meters'] = df['square_meter_build'].replace(0, pd.NA).combine_first(df['square_meters'])
    cols = ['city', 'pct', 'price', 'rooms', 'square_meters',
            'is_agency', 'neighborhood', 'street', 'street_num',
            'parking', 'balconies',
            'asset_status', 'asset_type', 'info_text', 'img_url']
    df = df[cols].sort_values('pct', ascending=True)
    return df


def format_telegram(idx, sr, asset_type):
    agency_str = "\n<b>מתיווך</b>" if sr['is_agency'] else ""
    rooms_str = int(sr['rooms']) if sr['rooms'].is_integer() else sr['rooms']
    price_meter_str = f"{sr['square_meters']:,.0f} מ״ר ({sr['price'] / sr['square_meters']:,.0f}₪ למטר)"
    balcony_parking = ""
    if sr['parking'] > 0 or sr['balconies']:
        balcony_parking = f"<b>עם:</b> {'חניה' if sr['parking'] > 0 else ''} {'מרפסת' if sr['balconies'] else ''}" #
    text_info = sr['info_text'].replace('\n', ',')[:100]
    text_str = f"""
\n{idx}.<b>עיר:</b> {sr['city']}{agency_str}
<b>מחיר:</b> {sr['price']:,.0f}₪
<b>חדרים:</b> {rooms_str},  {price_meter_str}
<b>מצב:</b> {sr['asset_status']}
<b>הנחה:</b> {abs(sr['pct']):.2%}
{balcony_parking}
{text_info}
https://realestate1.up.railway.app/{asset_type}/?{sr['id']}"""
    return text_str


# def _format_config_str(c):
#     # min_price=4000, max_price=8000, min_rooms=3, max_rooms=4,
# #                    ai_price_pct_less_than=-0.05,
# #                    parking=True, balconies=True,  # is_agency=False,
# #                    asset_status=["משופץ", "חדש (גרו בנכס)", "חדש מקבלן (לא גרו בנכס)"],
# #                    ai_std_pct=0.07, asset_type="rent"
#     f"מחיר: [}{c['min_price']}, {c['max_price']}]"


def publish(df, config, limit=None):
    asset_type = config.get("asset_type").replace("forsale", "sale")
    asset_type_str = "<b>🏠דירות למכירה:</b>" if asset_type == "sale" else "<b>💰דירות להשכרה:</b>"
    asset_type_str += f"\n {config}"
    output_str = asset_type_str
    max_assets_per_msg = 5
    df = df.reset_index()
    print(f"publishing {len(df)} assets for {asset_type=}")
    if limit:
        df = df[:10]
    for idx, row in df.iterrows():
        idx = idx + 1
        output_str += format_telegram(idx, row, asset_type)
        if idx % max_assets_per_msg == 0:
            send_to_telegram_channel(output_str, group_id, bot_id)
            output_str = ""
    if len(df) and len(output_str):
        send_to_telegram_channel(output_str, group_id, bot_id)


def find_and_publish(config):
    df = filter_assets(config)
    publish(df, config)


def find_and_publish_run_all():
    find_and_publish(config_sale)
    find_and_publish(config_rent)


if __name__ == '__main__':
    find_and_publish_run_all()
