from fetch_data.daily_fetch import run_daily_job, run_nadlan_daily, pub_object
from scrape_nadlan.utils_insert import get_engine


def daily_forsale():
    type_ = 'forsale'
    path = f'resources/yad2_{type_}_df.pk'
    eng = get_engine()
    path_nadlan = "resources/df_nadlan_recent.pk"
    df = run_daily_job(type_, eng)
    df.to_pickle(path)
    with eng.connect() as conn:
        run_nadlan_daily(conn, 240, path_nadlan)
    pub_object(path)
    pub_object(path_nadlan)


if __name__ == '__main__':
    daily_forsale()
