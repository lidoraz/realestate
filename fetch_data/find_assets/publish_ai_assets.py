import pandas as pd
from fetch_data.find_assets.filter_assets import filter_assets_by_config, filter_assets_by_newly_published, \
    filter_assets_by_discount
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


def format_telegram(idx, sr, asset_type):
    max_text_limit = 100
    asset_type = asset_type.replace('forsale', 'sale')
    agency_str = "\n<b>מתיווך</b>" if sr['is_agency'] else ""
    rooms_str = int(sr['rooms']) if sr['rooms'].is_integer() else sr['rooms']
    price_meter_str = f"{sr['square_meters']:,.0f} מ״ר ({sr['price'] / sr['square_meters']:,.0f}₪ למטר)"
    balcony_parking = ""
    if sr['parking'] > 0 or sr['balconies']:
        balcony_parking = (f"\n<b>עם:</b> {'חניה' if sr['parking'] > 0 else ''}"
                           f" {'מרפסת' if sr['balconies'] else ''}")  #
    text_info = sr['info_text'].replace('\n', ',')
    text_info = text_info[:max_text_limit] + '...' if len(text_info) > max_text_limit else text_info

    recent_price_pct, recent_price_diff = sr.get('recent_price_pct'), sr.get('recent_price_diff')
    if recent_price_pct is not None:
        discount_str = f"\n<b>**הנחה במחיר:</b> {abs(recent_price_pct):.1%}-, ({abs(recent_price_diff):,.0f}₪)"
        discount_str += f"\n<b>**נצפה לראשונה:</b> {sr['date_added'].date()}"
    else:
        discount_str = ""
    text_str = f"""
{idx}.<b>עיר:</b> {sr['city']}{agency_str}
<b>מחיר:</b> {sr['price']:,.0f}₪
<b>חדרים:</b> {rooms_str},  {price_meter_str}
<b>מצב:</b> {sr['asset_status']}
<b>אחוז ממחיר AI מודל:</b> {abs(sr['ai_price_pct']):.1%}-{discount_str}{balcony_parking}
{text_info}
https://realestate1.up.railway.app/{asset_type}/?{sr['id']}"""
    return text_str


def publish(df, config, find_type, limit=None):
    asset_type = config.get("asset_type").replace("forsale", "sale")
    assert find_type in ("new", "discount"), 'must be one of ("new", "discount")'
    assert asset_type in ("sale", "rent"), 'must be one of ("sale", "rent")'

    asset_type_str = "<b>🏠דירות למכירה</b>" if asset_type == "sale" else "<b>💰דירות להשכרה</b>"
    asset_type_str += "\n"
    find_type_str = "ירידות מחיר!📣" if find_type == "discount" else "עלו לאחרונה!🆕"
    output_str = asset_type_str + find_type_str + "\n"
    max_assets_per_msg = 5
    df = df.reset_index()
    print(f"publishing {len(df)} assets for {asset_type=}, {find_type=}")
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


def publish_once_a_week(config):
    from datetime import datetime
    import json
    isoweekday = datetime.now().date().isoweekday()
    if isoweekday == 1:  # sunday
        msg = f"'{config['asset_type']}' config details:\n" + json.dumps(config, ensure_ascii=False)
        send_to_telegram_channel(msg, group_id, bot_id)


def find_and_publish(config):
    df = pd.read_pickle(f"resources/yad2_{config['asset_type']}_df.pk")
    df = filter_assets_by_config(df, config)
    days_back = 1  # should be always 1

    df_new = filter_assets_by_newly_published(df, days_back=days_back)
    df_dis = filter_assets_by_discount(df, min_discount_pct=0.03, days_back=days_back)
    # Send config..
    publish_once_a_week(config)

    publish(df_new, config, find_type="new")
    publish(df_dis, config, find_type="discount")


def find_and_publish_run_all():
    print("find_and_publish_run_all")
    find_and_publish(config_sale)
    find_and_publish(config_rent)


if __name__ == '__main__':
    def send_to_telegram_channel(a, b, c):  # overrides when running this
        print(a)


    find_and_publish_run_all()
