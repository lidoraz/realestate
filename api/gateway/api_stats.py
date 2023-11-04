import requests
import os
from ext.retry import retry
import json


# Think about adding cache here
def req_ratio_time_taken_cities(deal_type: str, min_samples: int = 200, days_back: int = 7):
    res = requests.post(f'{os.getenv("REAL_ESTATE_API")}/ratio_time_taken_cities',
                        json={'type': deal_type, 'min_samples': min_samples, 'days_back': days_back})
    if res.status_code == 200:
        return res.json()['data_ratio_time_taken_cities']
    return None


def req_timeseries_recent_quantiles(deal_type, time_interval, cities=None):
    assert time_interval in ("year", "month", "week")
    cities = [cities] if isinstance(cities, str) else cities  # convert to array
    data = {"type": deal_type, "time_interval": time_interval}
    if cities:
        suffix = "city"
        data["cities_str"] = json.dumps(cities, ensure_ascii=False)
    else:
        suffix = "all"
    res = requests.post(f'{os.getenv("REAL_ESTATE_API")}/timeseries_recent_quantiles_{suffix}',
                        json=data)
    if res.status_code == 200:
        return res.json()[f'data_timeseries_recent_quantiles_{suffix}']
    return None


@retry(5, 1)
def req_timeseries_nadlan_prices(time_interval: str = 'month', years_back: int = 5):
    res = requests.post(url=f'{os.getenv("REAL_ESTATE_API")}/timeseries_nadlan_prices',
                        json={'time_interval': time_interval, 'years_back': years_back})
    if res.status_code != 200:
        raise ValueError("Got invalid status code")
    return res.json()['data_timeseries_nadlan_prices']


@retry(5, 1)
def req_timeseries_sidebar(lat, long, rooms, dist_km=1.0):
    res = requests.post(f'{os.getenv("REAL_ESTATE_API")}/timeseries',
                        json=dict(lat=lat,
                                  long=long,
                                  rooms=rooms,
                                  dist_km=dist_km))
    if res.status_code != 200:
        raise ValueError("Got invalid status code")
    return res.json()


@retry(5, 1)
def req_remote_past_sales(deal, dist_km, n_months=6):
    data = dict(lat=deal['lat'],
                long=deal['long'],
                dist_km=dist_km,
                n_months=n_months,
                rooms=deal['rooms'])
    res = requests.post(f'{os.getenv("REAL_ESTATE_API")}/histogram', json=data)
    if res.status_code != 200:
        raise ValueError("Got invalid status code")
    past_sales = res.json()
    past_sales = dict(data_histogram=past_sales['data_histogram']['price_declared'],
                      days_back=n_months * 30)
    return past_sales
