from fetch_data.daily_fetch import run_daily_job
from fetch_data.utils import get_nadlan
from scrape_nadlan.utils_insert import get_engine


def run_nadlan_daily(conn, day_backs):
    df = get_nadlan(conn, day_backs)
    df.to_sql(f"dashboard_nadlan_recent", conn, if_exists="replace")
    df.to_pickle("resources/df_nadlan_recent.pk")


if __name__ == '__main__':
    type_ = 'forsale'
    eng = get_engine()
    with eng.connect() as conn:
        run_daily_job(type_, conn)
        run_nadlan_daily(conn, 210)
