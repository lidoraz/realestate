from fetch_data.daily_fetch import run_daily_job, pub_object
from scrape_nadlan.utils_insert import get_engine
import pandas as pd

def daily_rent():
    type_ = 'rent'
    path = f'resources/yad2_{type_}_df.pk'
    eng = get_engine()
    print(f"STARTED DAILY FETCH FOR {type_}")
    df= pd.read_pickle(path)
    # df = run_daily_job(type_, eng)
    df.to_pickle(path)
    # save_to_db(df, type_, eng, with_nadlan=False)
    pub_object(path)


if __name__ == '__main__':
    daily_rent()
