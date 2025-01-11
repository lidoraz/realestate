import pandas as pd
from fetch_data.find_assets.filter_assets import filter_assets_by_config, filter_assets_by_newly_published, \
    filter_assets_by_discount
import os
from fetch_data.find_assets.publish_ai_utils import publish
from ext.publish import send_to_telegram_channel
from ext.env import load_vault

wanted_neighborhoods = {'תל אביב יפו': ['ביצרון ורמת ישראל',
                                        'נחלת יצחק',
                                        'תל חיים',
                                        'גני שרונה, קרית הממשלה',
                                        'מונטיפיורי, הרכבת'],
                        'גבעתיים': [
                            # means everything is allowed
                            ## 'בורוכוב',
                            # 'גבעת הרמבם',
                            # 'שינקין',
                            # 'הל"ה',
                        ],
                        'רמת גן': ['חרוזים',
                                   'שכונת הראשונים',
                                  # 'שכונת גפן',
                                   'שכונת הותיקים',
                                   ]
                        }

config_rent = dict(min_price=4000, max_price=10000, min_rooms=3, max_rooms=4,
                   ai_price_pct_less_than=+0.05,
                   # must_balcony must_parking no_agency
                   must_parking=True, must_balcony=True, must_no_agency=False,
                   asset_status=["משופץ", "חדש (גרו בנכס)", "חדש מקבלן (לא גרו בנכס)"],
                   cities=[
                       "תל אביב יפו",
                       "רמת גן",
                       "גבעתיים"],
                   wanted_neighborhoods=wanted_neighborhoods,
                   ai_std_pct=0.07, asset_type="rent")
config_sale = dict(min_price=1_000_000, max_price=3_000_000, min_rooms=3, max_rooms=4,
                   ai_price_pct_less_than=-0.10,
                   must_parking=True,
                   must_balcony=True,
                   must_no_agency=False,
                   cities=[
                       'קרית מוצקין',
                       "תל אביב יפו",
                       "ראשון לציון",
                       "רמת גן",
                       "בת ים",
                       "חולון",
                       "אור יהודה",
                       "גבעתיים",
                       "הרצליה", ],
                   ai_std_pct=0.07, asset_type="forsale")

load_vault()
bot_id = os.getenv('TELEGRAM_BOT_ID') or os.getenv("TELEGRAM_TOKEN")
group_id = os.getenv('TELEGRAM_REALESTATE_DEALS_CHANNEL')
assert bot_id
assert group_id


def publish_once_a_week(config):
    from datetime import datetime
    import json
    isoweekday = datetime.now().date().isoweekday()
    if isoweekday == 0:  # sunday
        msg = f"'{config['asset_type']}' config details:\n" + json.dumps(config, ensure_ascii=False)
        send_to_telegram_channel(msg, group_id, bot_id)


def find_and_publish(config):
    df = pd.read_pickle(f"resources/yad2_{config['asset_type']}_df.pk")
    df['ai_price_pct'] = df['price'] / df['ai_price'] - 1
    df = filter_assets_by_config(df, config)
    days_back = 1  # should be always 1

    df_new = filter_assets_by_newly_published(df, days_back=days_back)
    df_dis = filter_assets_by_discount(df, min_discount_pct=0.03, days_back=days_back)
    # Send config..
    publish_once_a_week(config)
    asset_type = config.get("asset_type")
    publish(df_new, asset_type, find_type="new", group_id=group_id, bot_id=bot_id)
    publish(df_dis, asset_type, find_type="discount", group_id=group_id, bot_id=bot_id)


def find_and_publish_run_all():
    print("find_and_publish_run_all")
    find_and_publish(config_sale)
    find_and_publish(config_rent)


if __name__ == '__main__':
    # def send_to_telegram_channel(a, b, c):  # overrides when running this
    #     print(b, c)
    #     print(a)


    find_and_publish_run_all()
