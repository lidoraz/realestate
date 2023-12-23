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
default_ai_price_pct_less_than = 0  # -0.05
default_n_limit = 5


def parse_envs():
    ai_price_pct_less_than_env = os.getenv("TELEGRAM_BOT_AI_PRICE_PCT_LESS_THAN")
    n_limit_env = os.getenv("TELEGRAM_BOT_LIMIT_N_ASSETS")
    try:
        ai_price_pct_less_than = float(ai_price_pct_less_than_env)
        assert ai_price_pct_less_than < 1
        print(f"{ai_price_pct_less_than=} ENV? {ai_price_pct_less_than_env is None}")
    except:
        ai_price_pct_less_than = default_ai_price_pct_less_than
    try:
        n_limit = int(n_limit_env)
        assert n_limit > 0
        print(f"{n_limit=} ENV? {n_limit_env is None}")
    except:
        n_limit = default_n_limit
    return ai_price_pct_less_than, n_limit


def process_user_preferences(uid, config, asset_type,
                             df, days_back,
                             ai_price_pct_less_than, n_limit):
    asset_type = config['asset_type'] = asset_type
    config['ai_price_pct_less_than'] = ai_price_pct_less_than
    min_discount_pct = 0.03

    df = filter_assets_by_config(df, config)
    df_new = filter_assets_by_newly_published(df, days_back=days_back)
    df_dis = filter_assets_by_discount(df, min_discount_pct=min_discount_pct, days_back=days_back)

    if len(df_new):
        publish(df_new, config, find_type="new", group_id=uid, bot_id=bot_id, limit=n_limit)
    if len(df_dis):
        publish(df_dis, config, find_type="discount", group_id=uid, bot_id=bot_id, limit=n_limit)
    if len(df_new) or len(df_dis):
        print(f"PUBLISH: {uid=}, {asset_type=}, {len(df_new)=}, {len(df_dis)=}")


def _load_dataframes():
    df_sale = pd.read_pickle(f"resources/yad2_{'forsale'}_df.pk")
    df_sale['ai_price_pct'] = df_sale['price'] / df_sale['ai_price'] - 1
    df_rent = pd.read_pickle(f"resources/yad2_{'rent'}_df.pk")
    df_rent['ai_price_pct'] = df_rent['price'] / df_rent['ai_price'] - 1
    return df_sale, df_rent


def process_updated_user(user_config):
    name = user_config['name']
    uid = user_config['telegram_id']
    update_msg = "Thanks for updating preferences {}!\n  Come back later and remember to turn notifications on!".format(
        name)
    send_to_telegram_channel(update_msg, uid, bot_id)


def send_welcome_msg(uid, name, days_back):
    welcome_message = (
        "Hello {}!\n"
        "I'm your dedicated assistant, here to help you find your next apartment.\n"
        "I'll send you listings that align with your preferences.\n"
        "If you wish to make any changes, feel free to update your profile on the registration page.\n"
        "I'll search now for recent apartments you and notify for any findings.\n"
        "Come back later, and be sure to activate notifications!"
    ).format(name)
    send_to_telegram_channel(welcome_message, uid, bot_id)


def publish_for_new_user(user_config):
    user_config['is_new_user'] = True
    find_and_publish([user_config])


def get_all_users_db():
    df_all = select_all()
    all_configs = df_all.to_dict('records')
    return all_configs


def find_and_publish_for_all_users():
    all_configs = get_all_users_db()
    find_and_publish(all_configs)


def find_and_publish(user_configs):
    df_sale, df_rent = _load_dataframes()
    ai_price_pct_less_than, n_limit = parse_envs()
    days_back = DAYS_BACK
    for user in user_configs:
        uid = user['telegram_id']
        name = user['name']
        print(f"Processing user: {uid}, {name}")
        sale_options = user['sale_preferences']
        if user.get('is_new_user'):
            days_back = 4
            send_welcome_msg(uid, name, days_back)
        if sale_options is not None:
            process_user_preferences(uid, sale_options,
                                     "sale", df_sale, days_back=days_back,
                                     ai_price_pct_less_than=ai_price_pct_less_than,
                                     n_limit=n_limit)
        rent_options = user['rent_preferences']
        if rent_options is not None:
            process_user_preferences(uid, rent_options,
                                     "rent", df_rent, days_back=days_back,
                                     ai_price_pct_less_than=ai_price_pct_less_than,
                                     n_limit=n_limit)


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


def test_user_new():
    from ext.test_db_user import _get_user_data_1
    user_config = _get_user_data_1()
    publish_for_new_user(user_config)


def test_parse_env():
    ai_price_pct_less_than_expected = -0.05
    n_limit_expected = 10
    os.environ["TELEGRAM_BOT_AI_PRICE_PCT_LESS_THAN"] = str(ai_price_pct_less_than_expected)
    os.environ["TELEGRAM_BOT_LIMIT_N_ASSETS"] = str(n_limit_expected)
    ai_price_pct_less_than, n_limit_env = parse_envs()
    assert ai_price_pct_less_than == ai_price_pct_less_than_expected
    assert n_limit_env == n_limit_expected


if __name__ == '__main__':
    test_parse_env()
    os.environ['PRODUCTION'] = "False"  # "TRUE" # set before
    test_user_new()


    def send_to_telegram_channel(a, b, c):  # overrides when running this
        print(b, c)
        print(a)


    find_and_publish_for_all_users()
    # find_and_publish_run_all()
