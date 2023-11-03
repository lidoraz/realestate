import requests
import os
import logging
import time
import functools
import traceback


def retry(retry_num, retry_sleep_sec):
    """
    retry help decorator.
    :param retry_num: the retry num; retry sleep sec
    :return: decorator
    """

    def decorator(func):
        """decorator"""

        # preserve information about the original function, or the func name will be "wrapper" not "func"
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """wrapper"""
            for attempt in range(retry_num):
                try:
                    return func(*args, **kwargs)  # should return the raw function's return value
                except Exception as err:  # pylint: disable=broad-except
                    logging.error(err)
                    logging.error(traceback.format_exc())
                    time.sleep(retry_sleep_sec)
                logging.error("Trying attempt %s of %s.", attempt + 1, retry_num)
            logging.error("func %s retry failed", func)
            raise Exception('Exceed max retry num: {} failed'.format(retry_num))

        return wrapper

    return decorator


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
