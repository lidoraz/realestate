from fetch_data.daily_fetch import run_daily_job
from scrape_nadlan.utils_insert import get_engine

if __name__ == '__main__':
    type_ = 'rent'
    eng = get_engine()
    with eng.connect() as conn:
        run_daily_job(type_, conn)
