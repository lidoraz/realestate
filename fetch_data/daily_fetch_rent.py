from fetch_data.daily_fetch import run_daily_job, pub_object
from ext.env import get_pg_engine


def daily_rent():
    type_ = 'rent'
    path = f'resources/yad2_{type_}_df.pk'
    eng = get_pg_engine()
    print(f"STARTED DAILY FETCH FOR {type_}")
    df = run_daily_job(type_, eng)
    df.to_pickle(path)
    pub_object(path)


if __name__ == '__main__':
    daily_rent()
