from ext.publish import send_to_telegram_channel
import pandas as pd

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
    if recent_price_pct is not None and not pd.isna(recent_price_pct):
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


def publish(df, config, find_type, group_id, bot_id, limit=None):
    asset_type = config.get("asset_type").replace("forsale", "sale")
    assert find_type in ("new", "discount"), 'must be one of ("new", "discount")'
    assert asset_type in ("sale", "rent"), 'must be one of ("sale", "rent")'

    asset_type_str = "<b>🏠דירות למכירה</b>" if asset_type == "sale" else "<b>💰דירות להשכרה</b>"
    asset_type_str += "\n"
    find_type_str = "ירידות מחיר!📣" if find_type == "discount" else "עלו לאחרונה!🆕"
    output_str = asset_type_str + find_type_str + "\n"
    max_assets_per_msg = 5
    df = df.reset_index()
    print(f"publishing {len(df)}, limited to {limit} assets for {asset_type=}, {find_type=}")
    if limit:
        df = df[:limit]
    for idx, row in df.iterrows():
        idx = idx + 1
        output_str += format_telegram(idx, row, asset_type)
        if idx % max_assets_per_msg == 0:
            send_to_telegram_channel(output_str, group_id, bot_id)
            output_str = ""
    if len(df) and len(output_str):
        send_to_telegram_channel(output_str, group_id, bot_id)
