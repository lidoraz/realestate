from lambda_function import lambda_handler
import json

example_data_histogram = {'lat': 32.1310648182, 'long': 34.8633406364, 'dist_km': 5, 'rooms': 4.5, 'n_months': 6}
example_data_timeseries = {'lat': 32.1310648182, 'long': 34.8633406364, 'dist_km': 1.0, 'rooms': 3.5}
example_data_timeseries_recent_quantiles_city = {'type': 'rent', 'cities_str': '["בת ים", "רמת גן"]'}
example_data_timeseries_recent_quantiles_all = {'type': 'sale'}
example_data_ratio_time_taken_cities_1 = {'type': 'rent', 'min_samples': 300, 'days_back': 14}
example_data_ratio_time_taken_cities_2 = {'type': 'sale', 'min_samples': 200, 'days_back': 14}
example_data_today_both_rent_sale = {'limit': 15}


def test_api():
    import pandas as pd
    event = _gen_event(example_data_timeseries, '/timeseries')
    res = lambda_handler(event, None)
    res = json.loads(res['body'])
    all_lst = []
    for k in res.keys():
        df = pd.DataFrame.from_dict(res[k])
        all_lst.append((k, len(df)))
    assert all_lst == [('data_nadlan', 63),
                       ('data_recent', 21),
                       ('data_recent_rent', 24)]


def test_hist():
    import pandas as pd
    event = _gen_event(example_data_histogram, '/histogram')
    res = lambda_handler(event, None)
    res = json.loads(res['body'])
    df = pd.DataFrame.from_dict(res['data_histogram'])
    assert df.shape[1] == 1


def test_ratio_time_taken_cities_1():
    import pandas as pd
    event = _gen_event(example_data_ratio_time_taken_cities_1, '/ratio_time_taken_cities')
    res = lambda_handler(event, None)
    res = json.loads(res['body'])
    df = pd.DataFrame.from_dict(res['data_ratio_time_taken_cities'])
    assert df.shape[1] == 5


def test_ratio_time_taken_cities_2():
    import pandas as pd
    event = _gen_event(example_data_ratio_time_taken_cities_2, '/ratio_time_taken_cities')
    res = lambda_handler(event, None)
    res = json.loads(res['body'])
    df = pd.DataFrame.from_dict(res['data_ratio_time_taken_cities'])
    assert df.shape[1] == 5


def test_timeseries_recent_quantiles_city():
    import pandas as pd
    event = _gen_event(example_data_timeseries_recent_quantiles_city, '/timeseries_recent_quantiles_city')
    res = lambda_handler(event, None)
    res = json.loads(res['body'])
    df = pd.DataFrame.from_dict(res['data_timeseries_recent_quantiles_city'])
    assert df.shape[1] == 7


def test_timeseries_recent_quantiles_all():
    import pandas as pd
    event = _gen_event(example_data_timeseries_recent_quantiles_all, '/timeseries_recent_quantiles_all')
    res = lambda_handler(event, None)
    res = json.loads(res['body'])
    df = pd.DataFrame.from_dict(res['data_timeseries_recent_quantiles_all'])
    assert df.shape[1] == 6


def test_today_both_rent_sale():
    import pandas as pd
    event = _gen_event(example_data_timeseries_recent_quantiles_all, '/today_both_rent_sale')
    res = lambda_handler(event, None)
    res = json.loads(res['body'])
    df = pd.DataFrame.from_dict(res['data_today_both_rent_sale'])
    print(df)
    assert df.shape == (30, 16)


def _gen_event(data, path):
    event = {}
    data = json.dumps(data)
    event['requestContext'] = {"http": {"method": 'POST', "path": path}}
    event['body'] = data
    return event


if __name__ == '__main__':
    test_api()
    test_hist()
    test_ratio_time_taken_cities_1()
    test_ratio_time_taken_cities_2()
    test_timeseries_recent_quantiles_city()
    test_timeseries_recent_quantiles_all()
    test_today_both_rent_sale()
