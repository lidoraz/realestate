from fetch_data.daily_fetch import run_daily_job, run_nadlan_daily
from ext.publish import put_object_in_bucket
from ext.env import get_pg_engine


def daily_forsale():
    type_ = 'forsale'
    path = f'resources/yad2_{type_}_df.pk'
    df = run_daily_job(type_)
    df.to_pickle(path)
    put_object_in_bucket(path)
    run_nadlan()


def run_nadlan():
    path_nadlan = "resources/df_nadlan_recent.pk"
    eng = get_pg_engine()
    with eng.connect() as conn:
        run_nadlan_daily(conn, 240, path_nadlan)
    put_object_in_bucket(path_nadlan)


if __name__ == '__main__':
    daily_forsale()
