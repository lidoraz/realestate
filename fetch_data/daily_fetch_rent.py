from fetch_data.daily_fetch import run_daily_job
from ext.publish import put_object_in_bucket


def daily_rent(model_params):
    type_ = 'rent'
    path = f'resources/yad2_{type_}_df.pk'
    df = run_daily_job(type_, model_params)
    df.to_pickle(path)
    put_object_in_bucket(path)
