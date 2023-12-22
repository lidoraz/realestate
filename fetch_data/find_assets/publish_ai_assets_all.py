from fetch_data.find_assets.filter_assets import filter_assets_by_config, filter_assets_by_newly_published, \
    filter_assets_by_discount
from fetch_data.find_assets.publish_ai_utils import publish
from ext.db_user import select_all
import pandas as pd
import os
from ext.publish import send_to_telegram_channel

bot_id = os.getenv("TELEGRAM_BOT_REALESTATE_DEALS")
DAYS_BACK = 1
assert bot_id
print(f"{DAYS_BACK=}")


def process_user_preferences(uid, config, asset_type, df_sale, df_rent, days_back=DAYS_BACK):
    df = df_sale if asset_type == "sale" else df_rent
    config['asset_type'] = asset_type
    config['ai_std_pct'] = 0.07
    config['ai_price_pct_less_than'] = -0.12
    min_discount_pct = 0.03
    print("config:", config)
    df = filter_assets_by_config(df, config)
    df_new = filter_assets_by_newly_published(df, days_back=days_back)
    df_dis = filter_assets_by_discount(df, min_discount_pct=min_discount_pct, days_back=days_back)

    print(f"{uid=}, {asset_type=}, {len(df_new)=}, {len(df_dis)=}")
    limit = 5
    if len(df_new):
        publish(df_new, config, find_type="new", group_id=uid, bot_id=bot_id, limit=limit)
    if len(df_dis):
        publish(df_dis, config, find_type="discount", group_id=uid, bot_id=bot_id, limit=limit)


def _load_dataframes():
    df_sale = pd.read_pickle(f"resources/yad2_{'forsale'}_df.pk")
    df_rent = pd.read_pickle(f"resources/yad2_{'rent'}_df.pk")
    return df_sale, df_rent


def process_updated_user(user_config):
    name = user_config['name']
    uid = user_config['telegram_id']
    update_msg = "Thanks for updating preferences {}!\n  Come back later and remember to turn notifications on!".format(
        name)
    send_to_telegram_channel(update_msg, uid, bot_id)


def publish_for_new_user(user_config):
    df_sale, df_rent = _load_dataframes()
    days_back = 4
    name = user_config['name']
    uid = user_config['telegram_id']
    sale_options = user_config['sale_preferences']
    rent_options = user_config['rent_preferences']
    welcome_msg = "Welcome {}!\n You will now receive few assets from past {} days\n Come back later and remember to turn notifications on!".format(
        name, days_back)

    send_to_telegram_channel(welcome_msg, uid, bot_id)
    if sale_options is not None:
        process_user_preferences(uid, sale_options, "sale", df_sale, df_rent, days_back=days_back)
    if rent_options is not None:
        process_user_preferences(uid, rent_options, "rent", df_sale, df_rent, days_back=days_back)


def find_and_publish_for_all_users():
    df_sale, df_rent = _load_dataframes()
    df_all = select_all()

    for _, user in df_all.iterrows():
        uid = user['telegram_id']
        print("*" * 100, f"USER {uid}", "*" * 100)
        sale_options = user['sale_preferences']
        if sale_options is not None:
            process_user_preferences(uid, sale_options, "sale", df_sale, df_rent)
        rent_options = user['rent_preferences']
        if rent_options is not None:
            process_user_preferences(uid, rent_options, "rent", df_sale, df_rent)


def test_user(uid):
    from ext.env import load_vault
    load_vault()
    from ext.env import get_pg_engine
    from sqlalchemy.orm import Session
    from ext.db_user import _get_user_record
    with Session(get_pg_engine()) as session:
        user_data = {'telegram_id': uid}
        user_config = _get_user_record(session, user_data)
        publish_for_new_user(user_config.__dict__)


if __name__ == '__main__':
    test_user(None)
    exit(0)
    # def send_to_telegram_channel(a, b, c):  # overrides when running this
    #     print(b, c)
    #     print(a)
    # os.environ['PRODUCTION'] = "TRUE" # set before
    find_and_publish_for_all_users()
    # find_and_publish_run_all()
