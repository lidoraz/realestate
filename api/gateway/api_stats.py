import requests
import os


# Think about adding cache here
def req_ratio_time_taken_cities(deal_type: str, min_samples: int = 200, days_back: int = 7):
    res = requests.post(f'{os.getenv("REAL_ESTATE_API")}/ratio_time_taken_cities',
                        json={'type': deal_type, 'min_samples': min_samples, 'days_back': days_back})
    if res.status_code == 200:
        return res.json()['data_ratio_time_taken_cities']
    return None


def req_timeseries_recent_quantiles(deal_type, time_interval, cities=None):
    import json
    assert time_interval in ("year", "month", "week")
    cities = [cities] if isinstance(cities, str) else cities # convert to array
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


def req_timeseries_nadlan_prices(time_interval: str = 'month', years_back: int = 5):
    res = requests.post(f'{os.getenv("REAL_ESTATE_API")}/timeseries_nadlan_prices',
                        json={'time_interval': time_interval, 'years_back': years_back})
    if res.status_code == 200:
        return res.json()['data_timeseries_nadlan_prices']
    return None

# TODO: ADD get_sidebar_plots api calls in a seperate file here
