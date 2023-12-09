from fetch_data.daily_fetch import run_daily_job
from ext.publish import put_object_in_bucket
from ext.env import get_pg_engine


def daily_rent():
    type_ = 'rent'
    path = f'resources/yad2_{type_}_df.pk'
    df = run_daily_job(type_)
    df.to_pickle(path)
    put_object_in_bucket(path)


if __name__ == '__main__':
    daily_rent()
